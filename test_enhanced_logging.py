#!/usr/bin/env python3
"""
Test script to demonstrate enhanced logging capabilities.
This simulates what you'll see when the proxy filters requests.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ollama_context_filter_proxy import filter_system_prompt, ENABLE_DETAILED_LOGGING

# Sample OpenCode context (realistic example)
SAMPLE_MESSAGES = [
    {
        "role": "system",
        "content": """You are a helpful coding assistant.

<project>
  src/
    main.py
    utils.py
    config.py
  tests/
    test_main.py
  README.md
  requirements.txt
</project>

<env>
  Working directory: /Users/morgan/project
  Is directory a git repo: yes
  Platform: darwin
  Today's date: Wed Nov 26 2025
  Git branch: main
  Git status: clean
</env>

Instructions from: AGENTS.md

You are a specialized subagent for code generation.
Follow these rules:
1. Write clean, idiomatic code
2. Include type hints
3. Add docstrings
4. Write tests

[... 5000 more lines of instructions ...]

Now, help the user with their coding task.""",
    },
    {"role": "user", "content": "Write a function to calculate fibonacci numbers"},
]


def main():
    print("=" * 80)
    print("ENHANCED LOGGING TEST")
    print("=" * 80)
    print()
    print("Testing with llama3.2:1b (small model - SHOULD filter)")
    print()

    # Test with small model
    filtered_messages, stats = filter_system_prompt(SAMPLE_MESSAGES, "llama3.2:1b")

    print("\n" + "=" * 80)
    print("STATS RETURNED:")
    print("=" * 80)
    print(f"Is small model: {stats['is_small_model']}")
    print(f"Original size: {stats['original_size']} chars")
    print(f"Filtered size: {stats['filtered_size']} chars")
    print(
        f"Reduction: {((stats['original_size'] - stats['filtered_size']) / stats['original_size'] * 100):.1f}%"
    )
    print(f"Sections removed: {len(stats['sections_removed'])}")
    for section in stats["sections_removed"]:
        print(f"  - {section['name']}: {section['size']} chars")
    print(f"Filter time: {stats['time_ms']:.2f}ms")

    print("\n" + "=" * 80)
    print("Testing with qwen2.5:7b (large model - should NOT filter)")
    print("=" * 80)
    print()

    # Test with large model
    filtered_messages2, stats2 = filter_system_prompt(SAMPLE_MESSAGES, "qwen2.5:7b")

    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
