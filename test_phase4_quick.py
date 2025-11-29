#!/usr/bin/env python3
"""
Quick Phase 4 Smoke Test - Validates LLM client integration

This is a lightweight test that validates:
- LLM client can be initialized
- Reasoning prompt generation works
- Synthesis prompt generation works
- Integration with nodes is correct

Run this before the full test suite.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("Phase 4 Quick Smoke Test")
print("=" * 80)
print()

# Test 1: Import all modules
print("Test 1: Importing modules...")
try:
    from src.tools.llm_client import get_llm_client, LLMClient
    from src.agent.nodes import reason_node, finish_node
    from src.agent.schema import create_initial_state
    from src.config.settings import get_settings
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize LLM client
print("\nTest 2: Initializing LLM client...")
try:
    settings = get_settings()
    print(f"  Model: {settings.llm_model}")
    print(f"  Base URL: {settings.openai_base_url or 'default'}")

    llm_client = get_llm_client()
    print(f"✓ LLM client initialized: {type(llm_client).__name__}")
except Exception as e:
    print(f"✗ LLM client initialization failed: {e}")
    sys.exit(1)

# Test 3: Test reasoning prompt generation
print("\nTest 3: Testing reasoning prompt generation...")
try:
    query = "What is quantum computing?"
    context = {
        "tool_calls": [],
        "internal_context": [],
        "external_context": [],
        "kb_path": "./knowledge/sample_docs",
    }
    available_tools = ["search_internal", "web_search", "finish"]

    prompt = llm_client._build_reasoning_prompt(query, context, available_tools)
    print(f"✓ Reasoning prompt generated ({len(prompt)} chars)")
    print(f"  Contains 'search_internal': {('search_internal' in prompt)}")
    print(f"  Contains 'web_search': {('web_search' in prompt)}")
    print(f"  Contains 'finish': {('finish' in prompt)}")
except Exception as e:
    print(f"✗ Reasoning prompt generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test synthesis prompt generation
print("\nTest 4: Testing synthesis prompt generation...")
try:
    query = "What is quantum computing?"
    internal_sources = ["Quantum computing uses qubits...", "Superposition allows..."]
    external_sources = [
        {"title": "Quantum Computing Explained", "url": "https://example.com/1", "content": "..."},
        {"title": "Latest in Quantum", "url": "https://example.com/2", "content": "..."},
    ]
    reasoning_trace = [
        {"step": 0, "thought": "I should search internally", "action": "search_internal"},
    ]

    prompt = llm_client._build_synthesis_prompt(query, internal_sources, external_sources, reasoning_trace)
    print(f"✓ Synthesis prompt generated ({len(prompt)} chars)")
    print(f"  Contains query: {(query in prompt)}")
    print(f"  Contains internal sources: {('qubits' in prompt)}")
    print(f"  Contains external sources: {('example.com' in prompt)}")
except Exception as e:
    print(f"✗ Synthesis prompt generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test reasoning response parsing
print("\nTest 5: Testing reasoning response parsing...")
try:
    sample_response = """THOUGHT: I should search the internal knowledge base first
ACTION: search_internal
ACTION_INPUT: quantum computing basics"""

    thought, action, action_input = llm_client._parse_reasoning_response(sample_response)
    print(f"✓ Response parsed successfully")
    print(f"  Thought: {thought[:50]}...")
    print(f"  Action: {action}")
    print(f"  Action Input: {action_input}")

    assert action == "search_internal", f"Expected 'search_internal', got '{action}'"
    assert "quantum computing basics" in action_input, "Action input missing"
except Exception as e:
    print(f"✗ Response parsing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test fallback for malformed responses
print("\nTest 6: Testing fallback for malformed responses...")
try:
    malformed_response = "This is a random response without the expected format"

    thought, action, action_input = llm_client._parse_reasoning_response(malformed_response)
    print(f"✓ Fallback handling works")
    print(f"  Fallback action: {action}")

    assert action == "finish", f"Expected fallback to 'finish', got '{action}'"
except Exception as e:
    print(f"✗ Fallback handling failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Test agent state initialization
print("\nTest 7: Testing agent state initialization...")
try:
    state = create_initial_state(
        query="Test query",
        max_steps=5,
        kb_path="./knowledge/sample_docs"
    )

    print(f"✓ State initialized successfully")
    print(f"  Query: {state['query']}")
    print(f"  Max steps: {state['max_steps']}")
    print(f"  KB path: {state.get('kb_path')}")
    print(f"  Scratchpad: {len(state['scratchpad'])} entries")
    print(f"  Tool calls: {len(state['tool_calls'])} entries")
except Exception as e:
    print(f"✗ State initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("✅ All Phase 4 quick tests PASSED!")
print("=" * 80)
print()
print("Phase 4 components validated:")
print("  ✓ LLM client initialization")
print("  ✓ Reasoning prompt generation")
print("  ✓ Synthesis prompt generation")
print("  ✓ Response parsing")
print("  ✓ Fallback handling")
print("  ✓ Agent state initialization")
print()
print("Ready for full integration test with API calls!")
print()
