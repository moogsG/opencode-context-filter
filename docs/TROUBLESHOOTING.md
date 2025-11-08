# Troubleshooting Guide

Common issues and solutions for OpenCode Context Filter Proxy.

## Installation Issues

### Issue: Port 11435 Already in Use

**Error**: "Address already in use"

**Solution**:
```bash
# Find and kill process on port 11435
lsof -ti:11435 | xargs kill -9

# Wait a moment
sleep 2

# Try again
opencode
```

### Issue: Permission Denied on Scripts

**Error**: "Permission denied: ./scripts/install.sh"

**Solution**:
```bash
chmod +x scripts/*.sh
chmod +x src/ollama_context_filter_proxy.py
```

### Issue: Python Not Found

**Error**: "python3: command not found"

**Solution**:
```bash
# Check Python installation
which python3

# Install Python 3.6+ if missing
sudo apt-get install python3  # Ubuntu/Debian
brew install python3           # macOS
```

## Configuration Issues

### Issue: OpenCode Can't Connect to Proxy

**Error**: "Connection refused to http://localhost:11435"

**Diagnosis**:
```bash
# Check if proxy is running
ps aux | grep ollama_context_filter | grep -v grep

# Check proxy logs
tail -20 /tmp/ollama_context_filter.log

# Test proxy manually
curl http://localhost:11435/api/tags
```

**Solutions**:

1. **Proxy not running**:
   ```bash
   python3 src/ollama_context_filter_proxy.py &
   ```

2. **Wrong port in config**:
   ```bash
   # Verify OpenCode config
   cat ~/.config/opencode/opencode.json | grep baseURL
   # Should show: "baseURL": "http://localhost:11435/v1"
   ```

3. **Firewall blocking port**:
   ```bash
   # Allow port 11435
   sudo ufw allow 11435/tcp  # Ubuntu
   ```

### Issue: Filtering Not Occurring

**Symptom**: No `[FILTER]` messages in logs

**Diagnosis**:
```bash
# Monitor proxy logs
tail -f /tmp/ollama_context_filter.log | grep FILTER
```

**Solutions**:

1. **Check model name**:
   ```python
   # In src/ollama_context_filter_proxy.py
   SMALL_MODELS = [
       "llama3.2:1b",  # Exact match required
       # Add your model if missing
   ]
   ```

2. **Verify request path**:
   ```bash
   # Check proxy receives requests
   tail -f /tmp/ollama_context_filter.log | grep POST
   ```

3. **Check OpenCode configuration**:
   ```bash
   cat ~/.config/opencode/opencode.json | grep -A 5 ollama
   ```

## Runtime Issues

### Issue: Proxy Crashes on Startup

**Error**: Proxy exits immediately

**Diagnosis**:
```bash
# Run proxy in foreground to see errors
python3 src/ollama_context_filter_proxy.py
```

**Common causes**:

1. **Port already in use**: Kill existing process
2. **Python version too old**: Upgrade to Python 3.6+
3. **Missing dependencies**: Should not occur (no external deps)

### Issue: Slow Response Times

**Symptom**: Requests still take 5-8 seconds

**Diagnosis**:
```bash
# Check if filtering is happening
grep FILTER /tmp/ollama_context_filter.log | tail -5
```

**Solutions**:

1. **Proxy not being used**:
   ```bash
   # Verify OpenCode uses port 11435
   netstat -tulpn | grep 11435
   ```

2. **Wrong model**:
   ```bash
   # Check subagent uses llama3.2:1b
   # In .opencode/config.json:
   "doc-reader": {
     "model": "ollama/llama3.2:1b"  # Verify this
   }
   ```

3. **Ollama slow**:
   ```bash
   # Test Ollama directly
   time curl -X POST http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"llama3.2:1b","messages":[{"role":"user","content":"Hi"}]}'
   ```

### Issue: High Memory Usage

**Symptom**: Proxy uses >100MB RAM

**Diagnosis**:
```bash
ps aux | grep ollama_context_filter
```

**Solutions**:

1. **Multiple instances running**:
   ```bash
   # Kill all instances
   pkill -f ollama_context_filter_proxy
   
   # Start single instance
   python3 src/ollama_context_filter_proxy.py &
   ```

2. **Memory leak** (unlikely):
   ```bash
   # Restart proxy periodically
   kill $(cat /tmp/ollama_context_filter.pid)
   python3 src/ollama_context_filter_proxy.py &
   ```

## Integration Issues

### Issue: Wrapper Doesn't Start Proxy

**Symptom**: Proxy never starts when running `opencode`

**Diagnosis**:
```bash
# Run wrapper with debug
bash -x scripts/opencode-wrapper.sh --help
```

**Solutions**:

1. **Wrong path in wrapper**:
   ```bash
   # Edit scripts/opencode-wrapper.sh
   PROXY_SCRIPT="/correct/path/to/src/ollama_context_filter_proxy.py"
   ```

2. **Alias not set**:
   ```bash
   # Check alias
   alias | grep opencode
   
   # Add if missing
   echo 'alias opencode="/path/to/scripts/opencode-wrapper.sh"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Issue: Tests Fail

**Error**: Test suite reports failures

**Diagnosis**:
```bash
# Run tests with verbose output
python3 tests/test_basic.py
```

**Common failures**:

1. **Ollama not running**:
   ```bash
   # Start Ollama
   ollama serve &
   sleep 5
   ```

2. **Model not available**:
   ```bash
   # Pull model
   ollama pull llama3.2:1b
   ```

3. **Proxy port in use**:
   ```bash
   # Free port
   lsof -ti:11435 | xargs kill -9
   ```

## Performance Issues

### Issue: Token Reduction Less Than Expected

**Symptom**: Only 20-30% reduction instead of 60-99%

**Diagnosis**:
```bash
# Check filtering logs
grep FILTER /tmp/ollama_context_filter.log | tail -10
```

**Solutions**:

1. **Context already small**:
   - Some prompts naturally have less context
   - Reduction depends on repository size

2. **Filtering not aggressive enough**:
   ```python
   # Edit src/ollama_context_filter_proxy.py
   # Review filter_system_prompt() function
   ```

## Debugging Tools

### Enable Debug Logging

Edit `src/ollama_context_filter_proxy.py`:

```python
# Add at top of proxy_request() method
print(f"[DEBUG] Path: {self.path}", file=sys.stderr, flush=True)
print(f"[DEBUG] Model: {model_name}", file=sys.stderr, flush=True)
print(f"[DEBUG] Messages count: {len(messages)}", file=sys.stderr, flush=True)
```

### Test Proxy Directly

```bash
# Send test request
curl -X POST http://localhost:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "system", "content": "Very long context here..."},
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

### Monitor Network Traffic

```bash
# Watch requests to proxy
sudo tcpdump -i lo -A 'tcp port 11435'
```

## Getting Help

If issues persist:

1. **Check logs**:
   ```bash
   cat /tmp/ollama_context_filter.log
   ```

2. **Run all tests**:
   ```bash
   python3 tests/test_basic.py
   python3 tests/test_realistic.py
   ```

3. **Create GitHub issue** with:
   - Error message
   - Proxy logs
   - OpenCode configuration
   - Test results
   - System information (OS, Python version)

4. **Upstream support**:
   - OpenCode issues: https://github.com/sst/opencode/issues
   - Feature request: https://github.com/sst/opencode/issues/4096

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Address already in use" | Port 11435 occupied | Kill process: `lsof -ti:11435 \| xargs kill -9` |
| "Connection refused" | Proxy not running | Start manually: `python3 src/ollama_context_filter_proxy.py &` |
| "Permission denied" | Script not executable | `chmod +x scripts/*.sh` |
| "No such file" | Wrong path | Update PROXY_SCRIPT in wrapper |
| "python3: not found" | Python not installed | `sudo apt-get install python3` |
