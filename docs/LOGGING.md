# Enhanced Logging Guide

The Context Filter Proxy now includes comprehensive logging to help you understand exactly what's being filtered and what's being sent to Ollama.

## Quick Start

View real-time logs:
```bash
tail -f /tmp/ollama_context_filter.log
```

## Log Levels

### Detailed Logging (Default: ON)

Shows everything:
- Original system prompt preview
- Each section removed with size
- Full filtered content sent to Ollama
- Summary statistics
- Timing information

**Enable/Disable:**
Edit `src/ollama_context_filter_proxy.py`:
```python
ENABLE_DETAILED_LOGGING = True  # Set to False for minimal logging
```

### Show Full Filtered Content (Default: ON)

Shows the complete filtered prompt being sent to Ollama.

**Enable/Disable:**
```python
SHOW_FULL_FILTERED_CONTENT = True  # Set to False to show preview only
```

## Log Format

### Filter Start
```
================================================================================
[FILTER START] Model: llama3.2:1b | Time: 14:58:37
================================================================================
```

### Original Content
```
[ORIGINAL SYSTEM PROMPT] 45234 chars (~11308 tokens)
Preview: You are Claude Code, Anthropic's official CLI...
```

### Removed Sections
```
[REMOVED] <project> section: 12456 chars (~3114 tokens)
  Preview: <project>
  src/
    main.py
    utils.py
  ...

[REMOVED] <env> section: 234 chars (~58 tokens)
  Preview: <env>
  Working directory: /Users/morgan/project
  ...

[REMOVED] Instructions section: 15234 chars (~3808 tokens)
  Preview: Instructions from: AGENTS.md
  ...
```

### Filtered Content (Sent to Ollama)
```
[FILTERED SYSTEM PROMPT] 456 chars (~114 tokens)
Content being sent to Ollama:
--------------------------------------------------------------------------------
You are a helpful coding assistant.

<env>
  Working directory: (current directory)
  Platform: linux
  Today's date: (current date)
</env>
--------------------------------------------------------------------------------
```

### Summary Statistics
```
[FILTER SUMMARY]
  Original size: 45234 chars (~11308 tokens)
  Filtered size: 456 chars (~114 tokens)
  Reduction: 99.0%
  Sections removed: 3
    - project: 12456 chars
    - env: 234 chars
    - instructions: 15234 chars
  Filter time: 1.23ms
================================================================================
```

### Passthrough (Large Models)
```
[PASSTHROUGH] Model 'qwen2.5:7b' not in SMALL_MODELS - no filtering
```

### User Messages
```
[PASSTHROUGH] user message: 47 chars (~11 tokens)
```

## Configuration Options

### `ENABLE_DETAILED_LOGGING`
- **Default:** `True`
- **Purpose:** Enable comprehensive logging
- **When to disable:** If logs are too verbose or affecting performance

### `SHOW_FULL_FILTERED_CONTENT`
- **Default:** `True`
- **Purpose:** Show complete filtered prompt sent to Ollama
- **When to disable:** If you only want to see statistics, not full content

### `MAX_LOG_CONTENT_LENGTH`
- **Default:** `500`
- **Purpose:** Maximum characters to show in removed section previews
- **Adjust:** Increase to see more context, decrease to reduce log size

## Use Cases

### Debugging Context Issues

**Problem:** Model responses are poor quality

**Solution:** Check logs to see if important context was removed:
```bash
tail -f /tmp/ollama_context_filter.log | grep REMOVED
```

### Optimizing Filter Rules

**Problem:** Want to remove more/less context

**Solution:** Review what's being sent:
```bash
tail -f /tmp/ollama_context_filter.log | grep "FILTERED SYSTEM PROMPT" -A 20
```

### Performance Analysis

**Problem:** Filtering seems slow

**Solution:** Check filter timing:
```bash
tail -f /tmp/ollama_context_filter.log | grep "Filter time"
```

### Verifying Model Detection

**Problem:** Unsure if model is being filtered

**Solution:** Check for FILTER START or PASSTHROUGH:
```bash
tail -f /tmp/ollama_context_filter.log | grep -E "FILTER START|PASSTHROUGH"
```

## Token Estimation

The proxy uses a simple estimation: **chars / 4 ≈ tokens**

This is approximate but sufficient for:
- Comparing before/after sizes
- Understanding reduction percentages
- Monitoring context usage

For exact token counts, use a proper tokenizer (e.g., `tiktoken`).

## Performance Impact

Detailed logging adds minimal overhead:
- **Filter time:** <2ms (measured)
- **Log writing:** Asynchronous (non-blocking)
- **Total impact:** <5ms per request

## Examples

### Example 1: Small Model (Filtered)
```
[FILTER START] Model: llama3.2:1b | Time: 14:58:37
[ORIGINAL SYSTEM PROMPT] 45234 chars (~11308 tokens)
[REMOVED] <project> section: 12456 chars (~3114 tokens)
[REMOVED] <env> section: 234 chars (~58 tokens)
[REMOVED] Instructions section: 15234 chars (~3808 tokens)
[FILTERED SYSTEM PROMPT] 456 chars (~114 tokens)
[FILTER SUMMARY]
  Reduction: 99.0%
  Filter time: 1.23ms
```

### Example 2: Large Model (Passthrough)
```
[PASSTHROUGH] Model 'qwen2.5:7b' not in SMALL_MODELS - no filtering
```

### Example 3: Multiple Messages
```
[FILTER START] Model: llama3.2:1b | Time: 14:58:37
[ORIGINAL SYSTEM PROMPT] 614 chars (~153 tokens)
[REMOVED] <project> section: 123 chars (~30 tokens)
[FILTERED SYSTEM PROMPT] 391 chars (~97 tokens)
[PASSTHROUGH] user message: 47 chars (~11 tokens)
[FILTER SUMMARY]
  Reduction: 36.3%
```

## Troubleshooting

### Logs Not Appearing

**Check proxy is running:**
```bash
ps aux | grep ollama_context_filter
```

**Check log file exists:**
```bash
ls -lh /tmp/ollama_context_filter.log
```

**Check stderr redirection:**
```bash
# Proxy should be started with:
python3 src/ollama_context_filter_proxy.py 2>&1 | tee /tmp/ollama_context_filter.log
```

### Too Much Logging

**Disable detailed logging:**
```python
ENABLE_DETAILED_LOGGING = False
```

**Or disable full content display:**
```python
SHOW_FULL_FILTERED_CONTENT = False
```

### Missing Sections in Logs

**Verify regex patterns match your content:**
```python
# Check patterns in filter_system_prompt()
r'<project>.*?</project>'
r'<env>.*?</env>'
r'Instructions from:.*?(?=\n\n|\Z)'
```

## Advanced Usage

### Custom Log Format

Edit `log_section()` function to customize output:
```python
def log_section(label, content, removed=False):
    # Your custom logging logic here
    pass
```

### Log to File Directly

Modify proxy startup to redirect stderr:
```bash
python3 src/ollama_context_filter_proxy.py 2>/tmp/ollama_context_filter.log &
```

### Parse Logs Programmatically

Logs use structured format for easy parsing:
```bash
# Extract all reductions
grep "Reduction:" /tmp/ollama_context_filter.log | awk '{print $2}'

# Extract filter times
grep "Filter time:" /tmp/ollama_context_filter.log | awk '{print $3}'
```

## Related Documentation

- [Setup Guide](SETUP.md) - Installation and configuration
- [Usage Guide](USAGE.md) - How to use the proxy
- [Technical Details](TECHNICAL.md) - Architecture and implementation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

## Feedback

If you have suggestions for improving logging, please open an issue on GitHub!
