#!/usr/bin/env python3
"""
Ollama Context Filter Proxy for OpenCode

This proxy intercepts requests to Ollama API and filters out excessive context
for small models like llama3.2:1b to improve performance and reduce token usage.

Usage:
    python3 ollama_context_filter_proxy.py

Then configure OpenCode to use http://localhost:11435/v1 instead of http://localhost:11434/v1
"""

import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import sys
import time
from datetime import datetime
import os

################################################################################
# CONFIGURATION
################################################################################

# Upstream Ollama server
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
PROXY_PORT = 11435

# Models that should have minimal context
# Add your small models here to enable filtering
SMALL_MODELS = [
    # Original small models
    "llama3.2:1b",
    "llama3.2-1b",
    "qwen2.5:1.5b",
    "qwen2.5-1.5b",
    # Morgan's models (added for filtering)
    "qwen3-large",
    "llama3-groq-tool-use-large",
    "phi4-mini-large",
    "granite4-large",
    # Add more models as needed:
    # "phi-2",
    # "tinyllama",
]

# Maximum context tokens for small models (not currently enforced)
MAX_CONTEXT_TOKENS = 2000

################################################################################
# LOGGING CONFIGURATION
################################################################################

# Enable detailed logging (shows what gets removed, what gets sent)
# Set to False for minimal logging (just summary stats)
ENABLE_DETAILED_LOGGING = True

# Show full filtered content being sent to Ollama
# Set to False to show only a preview (less verbose)
SHOW_FULL_FILTERED_CONTENT = True

# Disable filtering entirely (just log and pass through)
# Set to True to see what OpenCode sends WITHOUT any filtering
DISABLE_FILTERING = False

# Maximum characters to show in log previews for removed sections
MAX_LOG_CONTENT_LENGTH = 500

# Save complete filtered requests to file for inspection
SAVE_FILTERED_REQUESTS = True
FILTERED_REQUESTS_DIR = "/tmp/ollama_filtered_requests"

# Tool filtering configuration
ENABLE_TOOL_FILTERING = True  # ENABLED - NUCLEAR MODE!

# Remove duplicate index_* wrapper tools
REMOVE_DUPLICATE_TOOLS = True  # Remove all duplicate index_* tools

# Strip verbose descriptions from tools (keep only first 200 chars)
STRIP_TOOL_DESCRIPTIONS = True  # Reduce description verbosity

# Only include essential tools (removes rarely-used tools)
ESSENTIAL_TOOLS_ONLY = True  # NUCLEAR: Only 11 core OpenCode tools!

# Automatically increase context window for models
AUTO_INCREASE_CONTEXT = True
DEFAULT_CONTEXT_SIZE = 32768  # 32k tokens (enough for tools + messages)

# Essential tools to keep (if ESSENTIAL_TOOLS_ONLY is True)
ESSENTIAL_TOOLS = [
    "bash",
    "read",
    "write",
    "edit",
    "grep",
    "glob",
    "list",
    "task",
    "webfetch",
    "todoread",
    "todowrite",
]

################################################################################


def estimate_tokens(text):
    """
    Estimate token count (rough approximation: chars/4).

    Args:
        text: String to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


def log_section(label, content, removed=False):
    """
    Log a content section with size info.

    Args:
        label: Section label
        content: Section content
        removed: Whether this section was removed
    """
    if not ENABLE_DETAILED_LOGGING:
        return

    char_count = len(content)
    token_estimate = estimate_tokens(content)
    status = "REMOVED" if removed else "KEPT"

    # Truncate content for logging
    display_content = content[:MAX_LOG_CONTENT_LENGTH]
    if len(content) > MAX_LOG_CONTENT_LENGTH:
        display_content += f"... ({char_count - MAX_LOG_CONTENT_LENGTH} more chars)"

    print(
        f"[{status}] {label}: {char_count} chars (~{token_estimate} tokens)",
        file=sys.stderr,
        flush=True,
    )
    if removed and char_count > 0:
        print(f"  Preview: {display_content[:200]}...", file=sys.stderr, flush=True)


def filter_tools(tools, model_name):
    """
    Filter and optimize tool definitions to reduce token usage.

    Args:
        tools: List of tool definitions
        model_name: Name of the model

    Returns:
        Tuple of (filtered_tools, tool_stats)
    """
    if not ENABLE_TOOL_FILTERING:
        return tools, {"filtered": False}

    tool_stats = {
        "original_count": len(tools),
        "original_size": len(json.dumps(tools)),
        "removed_duplicates": 0,
        "stripped_descriptions": 0,
        "removed_tools": 0,
        "filtered_count": 0,
        "filtered_size": 0,
        "reduction_pct": 0.0,
    }

    filtered_tools = []
    seen_tools = set()

    for tool in tools:
        tool_name = tool.get("function", {}).get("name", "")

        # Remove duplicate index_* wrappers
        if REMOVE_DUPLICATE_TOOLS and tool_name.startswith("index_"):
            base_name = tool_name[6:]  # Remove "index_" prefix
            if base_name in seen_tools:
                tool_stats["removed_duplicates"] += 1
                continue

        # Filter to essential tools only
        if ESSENTIAL_TOOLS_ONLY and tool_name not in ESSENTIAL_TOOLS:
            tool_stats["removed_tools"] += 1
            continue

        # Strip verbose descriptions
        if STRIP_TOOL_DESCRIPTIONS:
            description = tool.get("function", {}).get("description", "")
            if len(description) > 200:
                tool["function"]["description"] = description[:200] + "..."
                tool_stats["stripped_descriptions"] += 1

        filtered_tools.append(tool)
        seen_tools.add(tool_name)

    tool_stats["filtered_count"] = len(filtered_tools)
    tool_stats["filtered_size"] = len(json.dumps(filtered_tools))

    # Calculate reduction percentage
    if tool_stats["original_size"] > 0:
        reduction_pct = (
            (tool_stats["original_size"] - tool_stats["filtered_size"])
            / tool_stats["original_size"]
            * 100
        )
    else:
        reduction_pct = 0.0
    tool_stats["reduction_pct"] = reduction_pct

    if ENABLE_DETAILED_LOGGING:
        print(f"\n[TOOL FILTERING]", file=sys.stderr, flush=True)
        print(
            f"  Original tools: {tool_stats['original_count']}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Filtered tools: {tool_stats['filtered_count']}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Removed duplicates: {tool_stats['removed_duplicates']}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Stripped descriptions: {tool_stats['stripped_descriptions']}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Removed tools: {tool_stats['removed_tools']}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Original size: {tool_stats['original_size']} chars (~{tool_stats['original_size'] // 4} tokens)",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Filtered size: {tool_stats['filtered_size']} chars (~{tool_stats['filtered_size'] // 4} tokens)",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Reduction: {tool_stats['reduction_pct']:.1f}%\n",
            file=sys.stderr,
            flush=True,
        )

    return filtered_tools, tool_stats


def save_filtered_request(messages, model_name, request_data):
    """
    Save the complete filtered request to a file for inspection.

    Args:
        messages: Filtered messages being sent to Ollama
        model_name: Name of the model
        request_data: Complete request data dictionary
    """
    if not SAVE_FILTERED_REQUESTS:
        return

    try:
        # Create directory if it doesn't exist
        os.makedirs(FILTERED_REQUESTS_DIR, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}_{model_name.replace(':', '_').replace('/', '_')}.txt"
        filepath = os.path.join(FILTERED_REQUESTS_DIR, filename)

        # Write complete request details
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"FILTERED REQUEST TO OLLAMA\n")
            f.write("=" * 80 + "\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {model_name}\n")
            f.write(f"Total Messages: {len(messages)}\n")
            f.write("=" * 80 + "\n\n")

            # Write each message
            for idx, msg in enumerate(messages, 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                f.write(f"\n{'=' * 80}\n")
                f.write(f"MESSAGE {idx}: {role.upper()}\n")
                f.write(f"{'=' * 80}\n")
                f.write(
                    f"Size: {len(content)} chars (~{estimate_tokens(content)} tokens)\n"
                )
                f.write(f"{'-' * 80}\n")
                f.write(content)
                f.write(f"\n{'-' * 80}\n")

            # Write summary
            total_chars = sum(len(m.get("content", "")) for m in messages)
            total_tokens = estimate_tokens(str(total_chars))

            f.write(f"\n\n{'=' * 80}\n")
            f.write(f"SUMMARY\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"Total Characters: {total_chars}\n")
            f.write(f"Estimated Tokens: ~{total_tokens}\n")
            f.write(f"Messages: {len(messages)}\n")
            f.write(f"{'=' * 80}\n")

            # Also save as JSON for programmatic access
            json_filename = filename.replace(".txt", ".json")
            json_filepath = os.path.join(FILTERED_REQUESTS_DIR, json_filename)
            with open(json_filepath, "w", encoding="utf-8") as jf:
                json.dump(request_data, jf, indent=2, ensure_ascii=False)

        print(
            f"[SAVED] Filtered request saved to: {filepath}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"[SAVED] JSON version saved to: {json_filepath}",
            file=sys.stderr,
            flush=True,
        )

    except Exception as e:
        print(
            f"[ERROR] Failed to save filtered request: {e}", file=sys.stderr, flush=True
        )


def filter_system_prompt(messages, model_name):
    """
    Filter system prompts to remove repository context for small models.

    Args:
        messages: List of message dictionaries
        model_name: Name of the model being used

    Returns:
        Tuple of (filtered_messages, filter_stats)
    """
    is_small_model = any(sm in model_name.lower() for sm in SMALL_MODELS)

    filter_stats = {
        "is_small_model": is_small_model,
        "sections_removed": [],
        "original_size": 0,
        "filtered_size": 0,
        "time_ms": 0,
        "total_messages": len(messages),
        "message_breakdown": [],
    }

    # If filtering is disabled, just log and pass through
    if DISABLE_FILTERING:
        if ENABLE_DETAILED_LOGGING:
            print(
                f"[FILTERING DISABLED] Passing through without changes",
                file=sys.stderr,
                flush=True,
            )
        return messages, filter_stats

    if not is_small_model:
        if ENABLE_DETAILED_LOGGING:
            print(
                f"[PASSTHROUGH] Model '{model_name}' not in SMALL_MODELS - no filtering",
                file=sys.stderr,
                flush=True,
            )
        return messages, filter_stats

    start_time = time.time()

    if ENABLE_DETAILED_LOGGING:
        # Show ALL messages BEFORE filtering WITH FULL CONTENT
        print(f"\n{'=' * 80}", file=sys.stderr, flush=True)
        print(
            f"ORIGINAL REQUEST - ALL MESSAGES (UNFILTERED):",
            file=sys.stderr,
            flush=True,
        )
        print(f"{'=' * 80}", file=sys.stderr, flush=True)
        total_before = 0
        for idx, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            size = len(content)
            tokens = estimate_tokens(content)
            total_before += size
            print(
                f"\nMessage {idx}/{len(messages)}: {role.upper()}",
                file=sys.stderr,
                flush=True,
            )
            print(
                f"  Size: {size} chars (~{tokens} tokens)", file=sys.stderr, flush=True
            )
            if size > 0:
                print(f"{'-' * 80}", file=sys.stderr, flush=True)
                print(content, file=sys.stderr, flush=True)
                print(f"{'-' * 80}", file=sys.stderr, flush=True)
        print(
            f"\nTOTAL ORIGINAL REQUEST: {total_before} chars (~{total_before // 4} tokens)",
            file=sys.stderr,
            flush=True,
        )
        print(f"{'=' * 80}\n", file=sys.stderr, flush=True)

    if ENABLE_DETAILED_LOGGING:
        print(f"\n{'=' * 80}", file=sys.stderr, flush=True)
        print(
            f"[FILTER START] Model: {model_name} | Time: {datetime.now().strftime('%H:%M:%S')}",
            file=sys.stderr,
            flush=True,
        )
        print(f"{'=' * 80}", file=sys.stderr, flush=True)

    filtered_messages = []

    for msg_idx, msg in enumerate(messages):
        if msg.get("role") == "system":
            original_content = msg.get("content", "")
            filter_stats["original_size"] = len(original_content)

            if ENABLE_DETAILED_LOGGING:
                print(
                    f"\n[ORIGINAL SYSTEM PROMPT] {len(original_content)} chars (~{estimate_tokens(original_content)} tokens)",
                    file=sys.stderr,
                    flush=True,
                )
                print(
                    f"Preview: {original_content[:300]}...\n",
                    file=sys.stderr,
                    flush=True,
                )

            content = original_content

            # Extract and remove <project> section
            project_match = re.search(
                r"<project>.*?</project>", content, flags=re.DOTALL
            )
            if project_match:
                project_content = project_match.group(0)
                log_section("<project> section", project_content, removed=True)
                filter_stats["sections_removed"].append(
                    {"name": "project", "size": len(project_content)}
                )
                content = re.sub(
                    r"<project>.*?</project>", "", content, flags=re.DOTALL
                )

            # Extract and remove <env> section
            env_match = re.search(r"<env>.*?</env>", content, flags=re.DOTALL)
            if env_match:
                env_content = env_match.group(0)
                log_section("<env> section", env_content, removed=True)
                filter_stats["sections_removed"].append(
                    {"name": "env", "size": len(env_content)}
                )
                content = re.sub(r"<env>.*?</env>", "", content, flags=re.DOTALL)

            # Extract and remove instruction files
            instructions_match = re.search(
                r"Instructions from:.*?(?=\n\n|\Z)", content, flags=re.DOTALL
            )
            if instructions_match:
                instructions_content = instructions_match.group(0)
                log_section("Instructions section", instructions_content, removed=True)
                filter_stats["sections_removed"].append(
                    {"name": "instructions", "size": len(instructions_content)}
                )
                content = re.sub(
                    r"Instructions from:.*?(?=\n\n|\Z)", "", content, flags=re.DOTALL
                )

            # Add minimal environment info
            minimal_env = """<env>
  Working directory: (current directory)
  Platform: linux
  Today's date: (current date)
</env>"""

            # Only add minimal env if there was content
            if content.strip():
                content = content.strip() + "\n\n" + minimal_env
            else:
                content = minimal_env

            filter_stats["filtered_size"] = len(content)

            if ENABLE_DETAILED_LOGGING:
                print(
                    f"\n[FILTERED SYSTEM PROMPT] {len(content)} chars (~{estimate_tokens(content)} tokens)",
                    file=sys.stderr,
                    flush=True,
                )
                if SHOW_FULL_FILTERED_CONTENT:
                    print(f"Content being sent to Ollama:", file=sys.stderr, flush=True)
                    print(f"{'-' * 80}", file=sys.stderr, flush=True)
                    print(content, file=sys.stderr, flush=True)
                    print(f"{'-' * 80}\n", file=sys.stderr, flush=True)
                else:
                    print(f"Preview: {content[:300]}...\n", file=sys.stderr, flush=True)

            msg["content"] = content
            filtered_messages.append(msg)
        else:
            # Non-system messages pass through
            filtered_messages.append(msg)
            if ENABLE_DETAILED_LOGGING:
                role = msg.get("role", "unknown")
                msg_content = msg.get("content", "")
                print(
                    f"[PASSTHROUGH] {role} message: {len(msg_content)} chars (~{estimate_tokens(msg_content)} tokens)",
                    file=sys.stderr,
                    flush=True,
                )

    filter_stats["time_ms"] = (time.time() - start_time) * 1000

    if ENABLE_DETAILED_LOGGING:
        # Show ALL messages AFTER filtering
        print(f"\n{'=' * 80}", file=sys.stderr, flush=True)
        print(
            f"ALL MESSAGES AFTER FILTERING (SENT TO OLLAMA):",
            file=sys.stderr,
            flush=True,
        )
        print(f"{'=' * 80}", file=sys.stderr, flush=True)
        total_after = 0
        for idx, msg in enumerate(filtered_messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            size = len(content)
            tokens = estimate_tokens(content)
            total_after += size
            print(
                f"\nMessage {idx}/{len(filtered_messages)}: {role.upper()}",
                file=sys.stderr,
                flush=True,
            )
            print(
                f"  Size: {size} chars (~{tokens} tokens)", file=sys.stderr, flush=True
            )
            if SHOW_FULL_FILTERED_CONTENT and size > 0:
                print(f"{'-' * 80}", file=sys.stderr, flush=True)
                print(content, file=sys.stderr, flush=True)
                print(f"{'-' * 80}", file=sys.stderr, flush=True)
            elif size > 0:
                preview = content[:200].replace("\n", " ")
                print(f"  Preview: {preview}...", file=sys.stderr, flush=True)
        print(
            f"\nTOTAL AFTER: {total_after} chars (~{estimate_tokens(str(total_after))} tokens)",
            file=sys.stderr,
            flush=True,
        )
        print(f"{'=' * 80}\n", file=sys.stderr, flush=True)

    if ENABLE_DETAILED_LOGGING:
        print(f"\n[FILTER SUMMARY]", file=sys.stderr, flush=True)
        orig_tokens = filter_stats["original_size"] // 4
        filt_tokens = filter_stats["filtered_size"] // 4
        print(
            f"  Original size: {filter_stats['original_size']} chars (~{orig_tokens} tokens)",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  Filtered size: {filter_stats['filtered_size']} chars (~{filt_tokens} tokens)",
            file=sys.stderr,
            flush=True,
        )
        reduction_pct = (
            (
                (filter_stats["original_size"] - filter_stats["filtered_size"])
                / filter_stats["original_size"]
                * 100
            )
            if filter_stats["original_size"] > 0
            else 0
        )
        print(f"  Reduction: {reduction_pct:.1f}%", file=sys.stderr, flush=True)
        print(
            f"  Sections removed: {len(filter_stats['sections_removed'])}",
            file=sys.stderr,
            flush=True,
        )
        for section in filter_stats["sections_removed"]:
            print(
                f"    - {section['name']}: {section['size']} chars",
                file=sys.stderr,
                flush=True,
            )
        print(
            f"  Filter time: {filter_stats['time_ms']:.2f}ms",
            file=sys.stderr,
            flush=True,
        )
        print(f"{'=' * 80}\n", file=sys.stderr, flush=True)

    return filtered_messages, filter_stats


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler that proxies to Ollama with context filtering."""

    def do_GET(self):
        """Handle GET requests (pass through to Ollama)."""
        self.proxy_request()

    def do_POST(self):
        """Handle POST requests (filter context for small models)."""
        self.proxy_request()

    def do_OPTIONS(self):
        """Handle OPTIONS requests (CORS preflight)."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def proxy_request(self):
        """Proxy the request to Ollama, filtering context for small models."""
        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""

            # Parse and filter for chat completions
            if self.path.startswith("/v1/chat/completions"):
                try:
                    data = json.loads(body.decode("utf-8")) if body else {}
                    model_name = data.get("model", "")
                    messages = data.get("messages", [])

                    # Filter messages for small models
                    filtered_messages, filter_stats = filter_system_prompt(
                        messages, model_name
                    )
                    data["messages"] = filtered_messages

                    # Filter tools to reduce token usage (DISABLED - these are OpenCode's tools!)
                    if ENABLE_TOOL_FILTERING and "tools" in data and data["tools"]:
                        filtered_tools, tool_stats = filter_tools(
                            data["tools"], model_name
                        )
                        data["tools"] = filtered_tools

                    # Automatically increase context window if needed
                    if AUTO_INCREASE_CONTEXT:
                        if "options" not in data:
                            data["options"] = {}
                        if "num_ctx" not in data["options"]:
                            data["options"]["num_ctx"] = DEFAULT_CONTEXT_SIZE
                            if ENABLE_DETAILED_LOGGING:
                                print(
                                    f"[CONTEXT] Set num_ctx to {DEFAULT_CONTEXT_SIZE} tokens",
                                    file=sys.stderr,
                                    flush=True,
                                )

                    # Save filtered request to file for inspection
                    save_filtered_request(filtered_messages, model_name, data)

                    # Legacy log for backwards compatibility (if detailed logging is off)
                    if not ENABLE_DETAILED_LOGGING and filter_stats["is_small_model"]:
                        original_tokens = sum(
                            len(m.get("content", "").split()) for m in messages
                        )
                        filtered_tokens = sum(
                            len(m.get("content", "").split()) for m in filtered_messages
                        )
                        if original_tokens != filtered_tokens:
                            print(
                                f"[FILTER] Model: {model_name}, Original tokens: ~{original_tokens}, Filtered tokens: ~{filtered_tokens}",
                                file=sys.stderr,
                                flush=True,
                            )

                    body = json.dumps(data).encode("utf-8")
                except json.JSONDecodeError:
                    pass

            # Forward to Ollama
            upstream_url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}{self.path}"
            headers = {
                k: v
                for k, v in self.headers.items()
                if k.lower() not in ["host", "content-length"]
            }
            headers["Content-Length"] = str(len(body))

            req = Request(upstream_url, data=body, headers=headers, method=self.command)

            try:
                with urlopen(req) as response:
                    # Send response
                    self.send_response(response.status)
                    for header, value in response.headers.items():
                        if header.lower() not in [
                            "transfer-encoding",
                            "content-encoding",
                        ]:
                            self.send_header(header, value)
                    self.end_headers()

                    # Stream response body
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        self.wfile.write(chunk)

            except HTTPError as e:
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(e.read())

        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_response = json.dumps({"error": str(e)})
            self.wfile.write(error_response.encode("utf-8"))

    def log_message(self, format, *args):
        """Log messages to stderr."""
        sys.stderr.write(f"[PROXY] {format % args}\n")


def main():
    """Start the proxy server."""
    server_address = ("", PROXY_PORT)
    httpd = HTTPServer(server_address, ProxyHandler)

    print(
        f"Ollama Context Filter Proxy running on http://localhost:{PROXY_PORT}",
        file=sys.stderr,
    )
    print(f"Forwarding to http://{OLLAMA_HOST}:{OLLAMA_PORT}", file=sys.stderr)
    print(
        f"Small models with context filtering: {', '.join(SMALL_MODELS)}",
        file=sys.stderr,
    )
    print(
        f"\nConfigure OpenCode to use: http://localhost:{PROXY_PORT}/v1",
        file=sys.stderr,
    )
    print(f"Press Ctrl+C to stop\n", file=sys.stderr)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down proxy...", file=sys.stderr)
        httpd.shutdown()


if __name__ == "__main__":
    main()
