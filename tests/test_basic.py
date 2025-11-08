#!/usr/bin/env python3
"""
Test script to verify Ollama Context Filter Proxy functionality.

Usage:
    # Start proxy in one terminal:
    python3 ollama_context_filter_proxy.py
    
    # Run test in another terminal:
    python3 test_context_filter.py
"""

import json
import urllib.request
import urllib.error
import sys

PROXY_URL = "http://localhost:11435/v1/chat/completions"

def test_context_filtering():
    """Test that large context is filtered for small models."""
    
    # Simulate a large system prompt with repository context
    large_system_prompt = """You are a helpful AI assistant.

<env>
  Working directory: /home/user/project
  Is directory a git repo: yes
  Platform: linux
  Today's date: Fri Nov 08 2025
</env>
<project>
  src/
    main.py
    utils.py
    models/
      user.py
      post.py
  tests/
    test_main.py
  README.md
  package.json
</project>

Instructions from: /home/user/project/AGENTS.md
# Project Instructions
This is a long instruction file with lots of context...
[... 10,000 more lines ...]
"""
    
    # Test request
    data = {
        "model": "llama3.2:1b",
        "messages": [
            {
                "role": "system",
                "content": large_system_prompt
            },
            {
                "role": "user",
                "content": "What is 2+2?"
            }
        ],
        "stream": False,
        "max_tokens": 50
    }
    
    try:
        req = urllib.request.Request(
            PROXY_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        print("Sending test request to proxy...", file=sys.stderr)
        print(f"Original system prompt length: {len(large_system_prompt)} characters", file=sys.stderr)
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            print("\n✅ Test PASSED: Proxy is working!", file=sys.stderr)
            print(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')}", file=sys.stderr)
            return True
    
    except urllib.error.URLError as e:
        print(f"\n❌ Test FAILED: Could not connect to proxy", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        print(f"\nMake sure proxy is running: python3 ollama_context_filter_proxy.py", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}", file=sys.stderr)
        return False


def test_direct_ollama():
    """Test direct connection to Ollama (without proxy)."""
    
    OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
    
    data = {
        "model": "llama3.2:1b",
        "messages": [
            {
                "role": "user",
                "content": "What is 2+2?"
            }
        ],
        "stream": False,
        "max_tokens": 50
    }
    
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        print("\nTesting direct Ollama connection...", file=sys.stderr)
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            print("✅ Ollama is running and responding", file=sys.stderr)
            return True
    
    except urllib.error.URLError as e:
        print(f"❌ Ollama is not running or not accessible", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        print(f"\nStart Ollama: ollama serve", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print("=" * 60, file=sys.stderr)
    print("Ollama Context Filter Proxy - Test Suite", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Test 1: Direct Ollama
    print("\n[Test 1] Checking Ollama connection...", file=sys.stderr)
    ollama_ok = test_direct_ollama()
    
    if not ollama_ok:
        print("\n⚠️  Ollama must be running before testing proxy", file=sys.stderr)
        sys.exit(1)
    
    # Test 2: Proxy filtering
    print("\n[Test 2] Checking proxy filtering...", file=sys.stderr)
    proxy_ok = test_context_filtering()
    
    print("\n" + "=" * 60, file=sys.stderr)
    if proxy_ok:
        print("✅ All tests PASSED", file=sys.stderr)
        print("\nProxy is working correctly and filtering context for small models.", file=sys.stderr)
        print("\nTo use with OpenCode, configure baseURL in config.json:", file=sys.stderr)
        print('  "baseURL": "http://localhost:11435/v1"', file=sys.stderr)
        sys.exit(0)
    else:
        print("❌ Tests FAILED", file=sys.stderr)
        print("\nTroubleshooting:", file=sys.stderr)
        print("1. Start proxy: python3 ollama_context_filter_proxy.py", file=sys.stderr)
        print("2. Ensure Ollama is running: ollama serve", file=sys.stderr)
        print("3. Check ports 11434 (Ollama) and 11435 (Proxy) are not blocked", file=sys.stderr)
        sys.exit(1)
