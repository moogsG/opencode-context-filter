# Usage Guide

How to use the OpenCode Context Filter Proxy in daily workflows.

## Basic Usage

### Starting OpenCode

Simply run:
```bash
opencode
```

The wrapper automatically:
1. Checks if proxy is running
2. Starts proxy if needed  
3. Launches OpenCode

### Using Subagents

Use subagents as normal:
```bash
# In OpenCode
@doc-reader summarise README.md
@codegen write a function to parse JSON
@editor fix grammar in chapter 12
```

The proxy automatically filters context for llama3.2:1b and qwen2.5:1.5b models.

## Monitoring

### View Proxy Logs

Real-time monitoring:
```bash
tail -f /tmp/ollama_context_filter.log
```

Filter-specific events:
```bash
tail -f /tmp/ollama_context_filter.log | grep FILTER
```

Example output:
```
[FILTER] Model: llama3.2:1b, Original tokens: ~483, Filtered tokens: ~176
[FILTER] Model: llama3.2:1b, Original tokens: ~385, Filtered tokens: ~142
```

### Check Proxy Status

```bash
# Check if running
ps aux | grep ollama_context_filter | grep -v grep

# View PID
cat /tmp/ollama_context_filter.pid

# Check logs
tail -20 /tmp/ollama_context_filter.log
```

## Manual Operations

### Start Proxy Manually

```bash
cd /path/to/opencode-context-filter
python3 src/ollama_context_filter_proxy.py
```

Leave running or use tmux:
```bash
# Start in background
tmux new-session -d -s ollama-filter 'python3 src/ollama_context_filter_proxy.py'

# Attach to view logs
tmux attach -t ollama-filter

# Detach: Ctrl+B, then D
```

### Stop Proxy

```bash
kill $(cat /tmp/ollama_context_filter.pid)
```

Proxy will restart automatically next time you run `opencode`.

### Run OpenCode Without Proxy

Use original OpenCode binary directly:
```bash
/home/gunnar/.opencode/bin/opencode
```

Or temporarily disable alias:
```bash
\opencode
```

## Advanced Usage

### Configure Filtered Models

Edit `src/ollama_context_filter_proxy.py`:

```python
SMALL_MODELS = [
    "llama3.2:1b",
    "llama3.2-1b",
    "qwen2.5:1.5b",
    "qwen2.5-1.5b",
    "phi-2",           # Add your model
    "tinyllama",       # Add another
]
```

### Change Proxy Port

Edit `scripts/opencode-wrapper.sh`:

```bash
PROXY_PORT=11435  # Change to desired port
```

Update OpenCode config:
```json
{
  "provider": {
    "ollama": {
      "options": {
        "baseURL": "http://localhost:YOUR_PORT/v1"
      }
    }
  }
}
```

### Custom Log Location

Edit `scripts/opencode-wrapper.sh`:

```bash
PROXY_LOG_FILE="/custom/path/to/proxy.log"
```

## Performance Monitoring

### Measure Response Time

Before (without proxy):
```bash
time @doc-reader summarise README.md
# ~8 seconds
```

After (with proxy):
```bash
time @doc-reader summarise README.md
# ~1 second
```

### View Token Reduction

Check proxy logs after each request:
```bash
tail -f /tmp/ollama_context_filter.log | grep FILTER
```

Expected reduction: 60-99% depending on context size.

## Best Practices

1. **Keep proxy running**: Let it run in background for best performance
2. **Monitor logs**: Regularly check for errors or issues
3. **Test after updates**: Run test suite after updating OpenCode or Ollama
4. **Backup config**: Keep a copy of your OpenCode configuration

## Common Workflows

### Daily Development

```bash
# Morning: Start OpenCode (proxy starts automatically)
opencode

# Use subagents throughout the day
# Proxy runs in background, filtering context

# Evening: OpenCode closes, proxy keeps running
```

### Debugging Session

```bash
# Terminal 1: Run OpenCode
opencode

# Terminal 2: Monitor proxy
tail -f /tmp/ollama_context_filter.log | grep FILTER

# Terminal 3: Check performance
watch -n 1 'ps aux | grep ollama_context_filter'
```

### Testing New Configuration

```bash
# Stop current proxy
kill $(cat /tmp/ollama_context_filter.pid)

# Edit configuration
vim src/ollama_context_filter_proxy.py

# Test manually
python3 src/ollama_context_filter_proxy.py

# In another terminal, run tests
python3 tests/test_basic.py
```

## Integration with CI/CD

The proxy can be used in automated environments:

```yaml
# Example GitHub Actions workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Start Ollama
        run: ollama serve &
      
      - name: Start Context Filter Proxy
        run: python3 src/ollama_context_filter_proxy.py &
      
      - name: Run OpenCode tests
        env:
          OPENCODE_BASE_URL: http://localhost:11435/v1
        run: opencode run "test the application"
```

## Next Steps

- See [Troubleshooting](TROUBLESHOOTING.md) for common issues
- Review [Technical Details](TECHNICAL.md) for architecture
- Check [Setup Guide](SETUP.md) for installation options
