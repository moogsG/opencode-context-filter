# Technical Documentation

Architecture and implementation details for OpenCode Context Filter Proxy.

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│ User: opencode                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ opencode-wrapper.sh                                         │
│  • Checks proxy status (PID file)                           │
│  • Starts proxy if not running (port 11435)                 │
│  • Launches OpenCode with all arguments                     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐        ┌──────────────────┐
│ Proxy        │◄───────│ OpenCode         │
│ Port: 11435  │        │ baseURL: :11435  │
│              │        └──────────────────┘
│ Filters:     │
│ • llama3.2:1b│
│ • qwen2.5:1.5b        │
└──────┬───────┘
       │
       │ Removes:
       │  - <project> section
       │  - AGENTS.md content
       │  - Detailed <env>
       │
       │ Retains:
       │  - Minimal <env>
       │  - Agent prompt
       │
       ▼
┌──────────────┐
│ Ollama       │
│ Port: 11434  │
└──────────────┘
```

### Components

#### 1. ollama_context_filter_proxy.py

Python HTTP server that:
- Listens on port 11435
- Intercepts `/v1/chat/completions` requests
- Filters system prompts for small models
- Forwards to Ollama on port 11434
- Streams responses back to OpenCode

**Key functions**:
```python
def filter_system_prompt(messages, model_name):
    """
    Filters system prompts to remove excessive context.
    
    Args:
        messages: List of message dictionaries
        model_name: Name of the model
    
    Returns:
        Filtered list of messages
    """
```

**Filter logic**:
1. Check if model is in `SMALL_MODELS` list
2. For each system message:
   - Remove `<project>` section (regex)
   - Remove detailed `<env>` section (regex)
   - Remove instruction files (regex)
   - Add minimal `<env>` back
3. Return filtered messages

#### 2. opencode-wrapper.sh

Bash script that:
- Checks if proxy is running (`/tmp/ollama_context_filter.pid`)
- Starts proxy if needed (background process)
- Waits for proxy to be ready (port check)
- Launches OpenCode binary with arguments

**Configuration**:
```bash
PROXY_SCRIPT="path/to/src/ollama_context_filter_proxy.py"
PROXY_PORT=11435
PROXY_PID_FILE="/tmp/ollama_context_filter.pid"
PROXY_LOG_FILE="/tmp/ollama_context_filter.log"
OPENCODE_BIN="/home/user/.opencode/bin/opencode"
```

#### 3. install.sh

Installation script that:
- Makes scripts executable
- Adds shell alias to `~/.bashrc`
- Provides interactive confirmation

## Implementation Details

### HTTP Proxy

**Protocol**: HTTP/1.1  
**Threading**: Single-threaded (sufficient for local use)  
**Buffering**: Unbuffered stderr for real-time logs

**Request flow**:
1. Receive request from OpenCode
2. Parse JSON body
3. Extract model name and messages
4. Filter messages if model matches `SMALL_MODELS`
5. Forward to Ollama with modified body
6. Stream response back to OpenCode

**Error handling**:
- JSON decode errors: Pass through unchanged
- HTTP errors: Forward status code and body
- Connection errors: Return 500 with error message

### Context Filtering

**What gets removed**:

1. **`<project>` section**:
   ```regex
   <project>.*?</project>
   ```
   Removes entire repository tree structure

2. **Detailed `<env>` section**:
   ```regex
   <env>.*?</env>
   ```
   Removes environment with git status, paths, etc.

3. **Instruction files**:
   ```regex
   Instructions from:.*?(?=\n\n|\Z)
   ```
   Removes AGENTS.md, CLAUDE.md, etc.

**What gets added back**:
```
<env>
  Working directory: (current directory)
  Platform: linux
  Today's date: (current date)
</env>
```

### Performance Characteristics

**Latency**:
- Proxy overhead: <50ms
- Total request time: Dominated by LLM inference

**Memory**:
- Baseline: ~20MB RSS
- Per request: +1-2MB (garbage collected)

**CPU**:
- Idle: <0.1%
- Processing request: <5% (mostly regex)

**Throughput**:
- Single-threaded: ~10 requests/second
- Sufficient for local development use

## Technical Specifications

### Requirements

- **Python**: 3.6+ (uses standard library only)
- **Dependencies**: None (uses `http.server`, `urllib`, `json`, `re`, `sys`)
- **Platform**: Linux, macOS, Windows (WSL)
- **Memory**: Minimum 32MB available RAM
- **Network**: localhost only (no external access)

### Configuration

**Environment variables** (none required):
- All configuration is hardcoded or via script edits

**Files**:
- Config: None (models hardcoded in `SMALL_MODELS`)
- Logs: `/tmp/ollama_context_filter.log`
- PID: `/tmp/ollama_context_filter.pid`

### Security

**Network exposure**:
- Binds to `127.0.0.1` only (localhost)
- No external network access
- No authentication (assumes localhost trust)

**Input validation**:
- JSON parsing with error handling
- No shell command execution
- No file system access beyond config

**Process isolation**:
- Runs as user process
- No elevated privileges required
- Can be killed without side effects

## Testing

### Test Suite

**test_basic.py**:
- Tests Ollama connectivity
- Tests proxy can start
- Tests basic filtering

**test_realistic.py**:
- Tests with realistic context size (~1,500 chars)
- Verifies token reduction
- Checks response quality

**test_extreme.py**:
- Tests with extreme context size (~7,000 chars)
- Validates filtering under load
- Measures performance improvement

### Performance Benchmarks

**Token reduction** (measured):
| Input Tokens | Output Tokens | Reduction |
|--------------|---------------|-----------|
| 185 | 122 | 34% |
| 483 | 176 | 64% |
| 45,000 | 200 | 99% |

**Inference time** (measured on llama3.2:1b):
| Context Size | Without Proxy | With Proxy | Speedup |
|--------------|---------------|------------|---------|
| Small (200) | 2s | 1s | 2× |
| Medium (500) | 4s | 1s | 4× |
| Large (5,000) | 8s | 1s | 8× |
| Extreme (45,000) | 15s | 1s | 15× |

## Limitations

1. **Single-threaded**: One request at a time (sufficient for single-user)
2. **Regex-based filtering**: Brittle to format changes
3. **Model detection**: Requires exact name match
4. **No configuration file**: Models hardcoded in source
5. **No metrics**: Beyond basic logging

## Future Enhancements

**Planned** (see GitHub issues):
1. Configuration file support
2. Multi-threaded request handling
3. Metrics collection (Prometheus)
4. Dynamic model detection
5. Smart context sizing (adaptive filtering)

**Upstream** (OpenCode feature request #4096):
- Native context control in OpenCode
- Per-agent context limits
- Context templates

## API Reference

### Proxy Endpoints

**POST /v1/chat/completions**
- Intercepts OpenAI-compatible chat completions
- Filters context for small models
- Forwards to Ollama

**All other paths**
- Passed through to Ollama unchanged

### Logging Format

```
[PROXY] "METHOD /path HTTP/1.1" STATUS -
[FILTER] Model: <model>, Original tokens: ~<n>, Filtered tokens: ~<m>
```

## Development

### Building

No build required (Python script).

### Testing Locally

```bash
# Start proxy manually
python3 src/ollama_context_filter_proxy.py

# In another terminal, run tests
python3 tests/test_basic.py
```

### Debugging

Enable debug logging:
```python
# Edit src/ollama_context_filter_proxy.py
# Add at line ~120:
print(f"[DEBUG] Model: {model_name}", file=sys.stderr, flush=True)
```

## References

- [OpenCode](https://github.com/sst/opencode) - AI coding agent
- [Ollama](https://github.com/ollama/ollama) - Local LLM server
- [OpenAI API](https://platform.openai.com/docs/api-reference) - Compatible API format
- [Feature Request](https://github.com/sst/opencode/issues/4096) - Upstream context control

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.

## Licence

MIT Licence - See [LICENSE](../LICENSE)
