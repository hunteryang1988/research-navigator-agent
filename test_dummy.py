#!/usr/bin/env python3
"""
Quick test script for Phase 1 dummy pipeline.

Run this to test the agent without needing the CLI installed.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.controller import run_agent

if __name__ == "__main__":
    print("Testing Research Navigator Agent - Phase 1 Dummy Mode\n")

    # Test query
    query = "What is quantum computing?"

    try:
        final_state = run_agent(
            query=query,
            kb_path=None,
            max_steps=3,
            output_file=None,
        )

        print("\n✓ Dummy pipeline test completed successfully!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
