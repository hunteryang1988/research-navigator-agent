# Quick Start Guide

## Phase 1 Complete - Dummy Pipeline Working!

The basic infrastructure is now in place and tested. The agent runs a dummy pipeline that demonstrates the graph structure.

## Available Commands

### Basic Usage

```bash
# Activate the virtual environment first
source venv/bin/activate

# Run a simple query
research-nav main "What is quantum computing?"

# Run with custom max steps
research-nav main "Compare quantum and classical computing" --max-steps 5

# Save output to file
research-nav main "Latest AI developments" --output report.md

# Run with knowledge base (Phase 2+ will make this functional)
research-nav main "Explain quantum entanglement" --kb ./knowledge/sample_docs
```

### Configuration Commands

```bash
# Check current configuration
research-nav config

# Check version
research-nav version

# Validate API keys before running
research-nav main "query" --check-config
```

### Direct Python Testing

If you prefer to test without activating venv:

```bash
# Run using venv python directly
venv/bin/research-nav main "Your query here"

# Or use the test script
venv/bin/python test_dummy.py
```

## Current Status (Phase 1)

### What Works

- ✅ Complete project structure
- ✅ LangGraph state machine setup
- ✅ Dummy nodes (reason, act_internal, act_external, finish)
- ✅ CLI with Typer (research-nav command)
- ✅ Configuration management with Pydantic Settings
- ✅ Rich console output with colors and formatting
- ✅ State flow through the graph
- ✅ Placeholder research brief generation

### What's Coming in Phase 2

- 🔜 Real RAG implementation with FAISS
- 🔜 Document loading from knowledge base
- 🔜 OpenAI embedding generation
- 🔜 Vector similarity search
- 🔜 Actual internal search results

## Next Steps

To proceed to Phase 2 (Internal RAG Implementation), confirm when ready. Phase 2 will:

1. Implement `tools/rag_loader.py` - Load documents and build vector store
2. Implement `tools/rag_search.py` - Search the vector store
3. Update `nodes.py` - Wire real RAG into act_internal_node
4. Test with the sample documents in `knowledge/sample_docs/`

## File Structure Created

```
src/
├── agent/
│   ├── schema.py         # AgentState TypedDict
│   ├── nodes.py          # Graph nodes (reason, act, finish)
│   ├── graph.py          # LangGraph construction
│   └── controller.py     # run_agent() orchestration
├── config/
│   └── settings.py       # Pydantic settings
└── cli/
    └── main.py          # Typer CLI entrypoint

knowledge/
├── README.md                    # KB management guide
└── sample_docs/
    ├── quantum_computing.md
    └── classical_computing.md

Configuration:
├── .env                  # Your API keys (not in git)
├── .env.example          # Template
├── pyproject.toml        # Package config
└── requirements.txt      # Dependencies
```

## Example Output

```
🤔 Reasoning Node (Step 0)
   Query: What is quantum computing?
   Thought: This is a placeholder reasoning step...
   Action: finish

✅ Finishing - Generating Research Brief
✨ Research brief generated!

Research Brief: What is quantum computing?

[Formatted markdown output with summary, findings, and sources]
```

## Troubleshooting

### Command not found: research-nav

Make sure you've activated the virtual environment:

```bash
source venv/bin/activate
```

Or use the full path:

```bash
venv/bin/research-nav main "query"
```

### Import errors

Ensure the package is installed:

```bash
pip install -e .
```

### Missing API keys warning

The dummy mode doesn't need API keys, but for Phase 2+ you'll need:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and TAVILY_API_KEY
```

Check configuration:

```bash
research-nav config
```

---

**Ready for Phase 2?** Let me know and I'll implement the real RAG system!
