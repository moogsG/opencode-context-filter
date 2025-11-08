# Setup Guide

Complete installation and configuration for OpenCode Context Filter Proxy.

## Installation

### Quick Install

```bash
git clone https://github.com/gunnarnordqvist/opencode-context-filter.git
cd opencode-context-filter
./scripts/install.sh
```

### Manual Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/gunnarnordqvist/opencode-context-filter.git
   cd opencode-context-filter
   ```

2. **Make scripts executable**
   ```bash
   chmod +x scripts/*.sh
   chmod +x src/ollama_context_filter_proxy.py
   ```

3. **Add alias to shell**
   ```bash
   echo 'alias opencode="$(pwd)/scripts/opencode-wrapper.sh"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Configuration

### Update OpenCode Configuration

Edit `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": {
        "baseURL": "http://localhost:11435/v1"
      },
      "models": {
        "llama3.2:1b": {
          "name": "Llama 3.2 (1B)"
        },
        "qwen2.5:1.5b": {
          "name": "Qwen2.5 (1.5B)"
        }
      }
    }
  }
}
```

**Critical change**: `"baseURL": "http://localhost:11435/v1"` (was `11434`, now `11435`)

### Update Script Paths

If you cloned to a non-standard location, update `scripts/opencode-wrapper.sh`:

```bash
# Change this line to match your installation path
PROXY_SCRIPT="/path/to/opencode-context-filter/src/ollama_context_filter_proxy.py"
```

## Verification

### Test Installation

```bash
# Run basic tests
python3 tests/test_basic.py
```

Expected output:
```
✅ All tests PASSED
```

### Test Wrapper

```bash
# Test wrapper starts proxy
./scripts/opencode-wrapper.sh --help
```

Expected output:
```
✓ Context filter proxy started successfully (PID: 12345)
✓ Filtering context for: llama3.2:1b, qwen2.5:1.5b
→ Launching OpenCode...
```

### Test OpenCode Integration

```bash
# Launch OpenCode
opencode

# In OpenCode, test a subagent
@doc-reader summarise README.md
```

Monitor proxy logs in another terminal:
```bash
tail -f /tmp/ollama_context_filter.log | grep FILTER
```

Expected output:
```
[FILTER] Model: llama3.2:1b, Original tokens: ~483, Filtered tokens: ~176
```

## Requirements

- **Python**: 3.6 or higher
- **OpenCode**: Any version
- **Ollama**: Running with llama3.2:1b or qwen2.5:1.5b models
- **Shell**: bash or compatible

## Next Steps

- Read [Usage Guide](USAGE.md) for daily usage
- See [Troubleshooting](TROUBLESHOOTING.md) for common issues
- Review [Technical Details](TECHNICAL.md) for architecture

## Uninstallation

```bash
# Remove alias from ~/.bashrc
sed -i '/opencode-context-filter/d' ~/.bashrc

# Stop proxy
kill $(cat /tmp/ollama_context_filter.pid)

# Remove repository
rm -rf /path/to/opencode-context-filter
```
