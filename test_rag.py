#!/usr/bin/env python3
"""
Test script for Phase 2 RAG functionality.

Tests document loading, vector store creation, and search.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.controller import run_agent

if __name__ == "__main__":
    print("=" * 80)
    print("Testing Phase 2 - RAG Search with Sample Documents")
    print("=" * 80)

    # Test query about quantum computing
    query = "What are the key differences between quantum and classical computing?"

    try:
        print("\n[TEST 1] Query with knowledge base")
        print(f"Query: {query}")
        print(f"KB: ./knowledge/sample_docs\n")

        final_state = run_agent(
            query=query,
            kb_path="./knowledge/sample_docs",
            max_steps=5,
            output_file=None,
        )

        print("\n" + "=" * 80)
        print("✓ Test 1 completed successfully!")
        print(f"  Internal chunks retrieved: {len(final_state['internal_context'])}")
        print(f"  Tool calls: {len(final_state['tool_calls'])}")

        # Show first chunk preview
        if final_state['internal_context']:
            first_chunk = final_state['internal_context'][0]
            preview = first_chunk[:200] + "..." if len(first_chunk) > 200 else first_chunk
            print(f"\n  First chunk preview:\n  {preview}")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
    print("All RAG tests passed! ✓")
    print("=" * 80)
