# Quick Reference - Enhanced Logging

## View Logs

```bash
# Real-time logs
tail -f /tmp/ollama_context_filter.log

# Last 50 lines
tail -50 /tmp/ollama_context_filter.log

# Search for specific content
grep "FILTER START" /tmp/ollama_context_filter.log
```

## Common Queries

```bash
# See what's being removed
tail -f /tmp/ollama_context_filter.log | grep REMOVED

# See what's being sent to Ollama
tail -f /tmp/ollama_context_filter.log | grep "Content being sent" -A 30

# See reduction percentages
tail -f /tmp/ollama_context_filter.log | grep "Reduction:"

# See filter timing
tail -f /tmp/ollama_context_filter.log | grep "Filter time:"

# See which models are filtered
tail -f /tmp/ollama_context_filter.log | grep "FILTER START"

# See which models pass through
tail -f /tmp/ollama_context_filter.log | grep "PASSTHROUGH"
```

## Configuration

Edit `src/ollama_context_filter_proxy.py`:

```python
# Show detailed logs (default: True)
ENABLE_DETAILED_LOGGING = True

# Show full filtered content (default: True)
SHOW_FULL_FILTERED_CONTENT = True

# Max chars in previews (default: 500)
MAX_LOG_CONTENT_LENGTH = 500
```

## Log Format

### Filter Event
```
[FILTER START] Model: llama3.2:1b | Time: 14:58:37
[ORIGINAL SYSTEM PROMPT] 45234 chars (~11308 tokens)
[REMOVED] <project> section: 12456 chars (~3114 tokens)
[FILTERED SYSTEM PROMPT] 456 chars (~114 tokens)
[FILTER SUMMARY]
  Reduction: 99.0%
  Filter time: 1.23ms
```

### Passthrough Event
```
[PASSTHROUGH] Model 'qwen2.5:7b' not in SMALL_MODELS - no filtering
```

## Test Logging

```bash
# Run test script
python3 test_enhanced_logging.py

# Check syntax
python3 -m py_compile src/ollama_context_filter_proxy.py
```

## Troubleshooting

### No logs appearing
```bash
# Check proxy is running
ps aux | grep ollama_context_filter

# Check log file
ls -lh /tmp/ollama_context_filter.log

# Restart proxy
pkill -f ollama_context_filter
python3 src/ollama_context_filter_proxy.py &
```

### Too much logging
```python
# Disable detailed logging
ENABLE_DETAILED_LOGGING = False

# Or just disable full content
SHOW_FULL_FILTERED_CONTENT = False
```

## Full Documentation

- [Logging Guide](docs/LOGGING.md) - Complete logging documentation
- [Setup Guide](docs/SETUP.md) - Installation
- [Usage Guide](docs/USAGE.md) - How to use
- [Enhancements](ENHANCEMENTS.md) - What's new
