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

# Upstream Ollama server
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
PROXY_PORT = 11435

# Models that should have minimal context
SMALL_MODELS = [
    "llama3.2:1b",
    "llama3.2-1b",
    "qwen2.5:1.5b",
    "qwen2.5-1.5b",
]

# Maximum context tokens for small models
MAX_CONTEXT_TOKENS = 2000


def filter_system_prompt(messages, model_name):
    """
    Filter system prompts to remove repository context for small models.
    
    Args:
        messages: List of message dictionaries
        model_name: Name of the model being used
    
    Returns:
        Filtered list of messages
    """
    is_small_model = any(sm in model_name.lower() for sm in SMALL_MODELS)
    
    if not is_small_model:
        return messages
    
    filtered_messages = []
    
    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            
            # Remove <project> section (repository tree)
            content = re.sub(r'<project>.*?</project>', '', content, flags=re.DOTALL)
            
            # Remove full <env> section and replace with minimal version
            content = re.sub(r'<env>.*?</env>', '', content, flags=re.DOTALL)
            
            # Remove AGENTS.md and other instruction files
            content = re.sub(r'Instructions from:.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)
            
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
            
            msg["content"] = content
            filtered_messages.append(msg)
        else:
            filtered_messages.append(msg)
    
    return filtered_messages


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
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Parse and filter for chat completions
            if self.path.startswith('/v1/chat/completions'):
                try:
                    data = json.loads(body.decode('utf-8')) if body else {}
                    model_name = data.get('model', '')
                    messages = data.get('messages', [])
                    
                    # Calculate original token count before filtering
                    original_tokens = sum(len(m.get('content', '').split()) for m in messages)
                    
                    # Filter messages for small models
                    filtered_messages = filter_system_prompt(messages, model_name)
                    data['messages'] = filtered_messages
                    
                    # Log filtering action
                    filtered_tokens = sum(len(m.get('content', '').split()) for m in filtered_messages)
                    if original_tokens != filtered_tokens:
                        print(f"[FILTER] Model: {model_name}, Original tokens: ~{original_tokens}, Filtered tokens: ~{filtered_tokens}", file=sys.stderr, flush=True)
                    
                    body = json.dumps(data).encode('utf-8')
                except json.JSONDecodeError:
                    pass
            
            # Forward to Ollama
            upstream_url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}{self.path}"
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ['host', 'content-length']}
            headers['Content-Length'] = str(len(body))
            
            req = Request(upstream_url, data=body, headers=headers, method=self.command)
            
            try:
                with urlopen(req) as response:
                    # Send response
                    self.send_response(response.status)
                    for header, value in response.headers.items():
                        if header.lower() not in ['transfer-encoding', 'content-encoding']:
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
            self.wfile.write(error_response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Log messages to stderr."""
        sys.stderr.write(f"[PROXY] {format % args}\n")


def main():
    """Start the proxy server."""
    server_address = ('', PROXY_PORT)
    httpd = HTTPServer(server_address, ProxyHandler)
    
    print(f"Ollama Context Filter Proxy running on http://localhost:{PROXY_PORT}", file=sys.stderr)
    print(f"Forwarding to http://{OLLAMA_HOST}:{OLLAMA_PORT}", file=sys.stderr)
    print(f"Small models with context filtering: {', '.join(SMALL_MODELS)}", file=sys.stderr)
    print(f"\nConfigure OpenCode to use: http://localhost:{PROXY_PORT}/v1", file=sys.stderr)
    print(f"Press Ctrl+C to stop\n", file=sys.stderr)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down proxy...", file=sys.stderr)
        httpd.shutdown()


if __name__ == "__main__":
    main()
