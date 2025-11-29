#!/usr/bin/env python3
"""
Test script for verbose logging functionality.

This will attempt to run the agent with verbose logging enabled.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.api_logger import set_verbose
from src.agent.controller import run_agent

if __name__ == "__main__":
    print("=" * 80)
    print("Testing Verbose Logging - Phase 2")
    print("=" * 80)
    print("\nThis test will show detailed API call logging including:")
    print("  • API call timing")
    print("  • Request parameters")
    print("  • Token estimates")
    print("  • Response details")
    print("  • Vector store operations")
    print("\n" + "=" * 80 + "\n")

    # Enable verbose mode
    set_verbose(True)

    # Test query
    query = "What is quantum computing?"

    try:
        print("Running with verbose logging enabled...\n")

        final_state = run_agent(
            query=query,
            kb_path="./knowledge/sample_docs",
            max_steps=3,
            output_file=None,
        )

        print("\n" + "=" * 80)
        print("✓ Test completed!")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
