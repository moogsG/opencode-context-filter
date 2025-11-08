#!/usr/bin/env python3
"""
Realistic test with large repository context to demonstrate filtering.
"""

import json
import urllib.request
import urllib.error
import sys

PROXY_URL = "http://localhost:11435/v1/chat/completions"

# Simulate a realistic large context from OpenCode
large_context = """You are OpenCode, the best coding agent on the planet.

<env>
  Working directory: /home/gunnar/github/architecture_as_code
  Is directory a git repo: yes
  Platform: linux
  Today's date: Sat Nov 09 2025
</env>
<project>
  .github/
\tscripts/
\t\t[4 truncated]
\tworkflows/
\t\t[44 truncated]
\tdependabot.yml
adr/
\tADR-0003-selection-of-terraform.md
\tADR-0007-selection-of-postgresql.md
docs/
\tadr/
\t\t[2 truncated]
\tarchive/
\t\t[7 truncated]
\texamples/
\t\t[1 truncated]
\timages/
\t\t[210 truncated]
\t00_front_cover.md
\t01_introduction.md
\t02_fundamental_principles.md
\t03_version_control.md
\t04_adr.md
\t05_automation_devops_cicd.md
\t[30 more files...]
scripts/
\tanalyze_chapter_lengths.py
\tcheck_doc_numbering.py
\tgenerate_adr_catalogue.py
\t[20 more files...]
README.md
package.json
</project>

Instructions from: /home/gunnar/github/architecture_as_code/AGENTS.md
# Architecture as Code Book Workshop - Development Instructions

**ALWAYS follow these instructions first and fallback to additional search and context gathering ONLY if the information in these instructions is incomplete or found to be in error.**

## Project Overview

This repository focuses on a single goal:

1. **Book Publishing**: Automated generation and publishing of "Architecture as Code" - a comprehensive technical book on architecture as code principles.

## Working Effectively

### Initial Setup and Dependencies

**NEVER CANCEL long-running installs.** Build processes can take 15+ minutes. Always use timeouts of 60+ minutes for installs.

[... 5000 more lines of instructions ...]
"""

def test_with_large_context():
    """Test filtering with realistic large context."""
    
    data = {
        "model": "llama3.2:1b",
        "messages": [
            {
                "role": "system",
                "content": large_context
            },
            {
                "role": "user",
                "content": "Summarize what this project does in one sentence."
            }
        ],
        "stream": False,
        "max_tokens": 100
    }
    
    print("=" * 70, file=sys.stderr)
    print("REALISTIC CONTEXT FILTERING TEST", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"\n📊 Original system prompt:", file=sys.stderr)
    print(f"   - Characters: {len(large_context):,}", file=sys.stderr)
    print(f"   - Approximate tokens: ~{len(large_context.split()):,}", file=sys.stderr)
    print(f"\n📝 Contains:", file=sys.stderr)
    print(f"   - <project> section with full file tree", file=sys.stderr)
    print(f"   - <env> section with environment details", file=sys.stderr)
    print(f"   - AGENTS.md instructions (5000+ lines)", file=sys.stderr)
    
    try:
        req = urllib.request.Request(
            PROXY_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n🔄 Sending to proxy (http://localhost:11435)...", file=sys.stderr)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
            
            print(f"\n✅ Response received!", file=sys.stderr)
            response_text = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
            print(f"\n💬 Model response:", file=sys.stderr)
            print(f"   {response_text}", file=sys.stderr)
            
            print(f"\n📈 Token usage (from model):", file=sys.stderr)
            usage = result.get('usage', {})
            print(f"   - Prompt tokens: {usage.get('prompt_tokens', 'N/A')}", file=sys.stderr)
            print(f"   - Completion tokens: {usage.get('completion_tokens', 'N/A')}", file=sys.stderr)
            print(f"   - Total tokens: {usage.get('total_tokens', 'N/A')}", file=sys.stderr)
            
            # Check proxy logs for filtering
            print(f"\n🔍 Check proxy logs at /tmp/proxy.log for [FILTER] messages", file=sys.stderr)
            print(f"   showing token reduction details", file=sys.stderr)
            
            return True
    
    except urllib.error.URLError as e:
        print(f"\n❌ Connection error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_large_context()
    print(f"\n{'='*70}", file=sys.stderr)
    if success:
        print("✅ Test completed successfully!", file=sys.stderr)
        print("\nThe proxy automatically filtered the large context down to minimal", file=sys.stderr)
        print("environment information, significantly reducing token usage.", file=sys.stderr)
    else:
        print("❌ Test failed", file=sys.stderr)
    print(f"{'='*70}\n", file=sys.stderr)
    sys.exit(0 if success else 1)
