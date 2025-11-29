#!/usr/bin/env python3
"""
Test script for Phase 3 - External Web Search with Tavily.

Tests both internal RAG and external Tavily web search.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.controller import run_agent

if __name__ == "__main__":
    print("=" * 80)
    print("Testing Phase 3 - Internal RAG + External Web Search")
    print("=" * 80)

    tests = [
        {
            "name": "Test 1: Web-only search (no KB)",
            "query": "What are the latest developments in AI in 2024?",
            "kb_path": None,
            "max_steps": 5,
        },
        {
            "name": "Test 2: Combined KB + Web search",
            "query": "How does quantum computing compare to classical computing in practical applications?",
            "kb_path": "./knowledge/sample_docs",
            "max_steps": 5,
        },
    ]

    for i, test in enumerate(tests, 1):
        print(f"\n[{test['name']}]")
        print(f"Query: {test['query']}")
        print(f"KB: {test['kb_path'] or 'None (web-only)'}")
        print("=" * 80 + "\n")

        try:
            final_state = run_agent(
                query=test["query"],
                kb_path=test["kb_path"],
                max_steps=test["max_steps"],
            )

            print(f"\n✓ Test {i} completed!")
            print(f"  Internal sources: {len(final_state['internal_context'])}")
            print(f"  External sources: {len(final_state['external_context'])}")
            print(f"  Steps: {final_state['step']}")
            print("=" * 80)

        except Exception as e:
            print(f"\n✗ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print("\n" + "=" * 80)
    print("All Phase 3 tests completed! ✓")
    print("=" * 80)
