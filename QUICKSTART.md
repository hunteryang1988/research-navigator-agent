# Research Navigator Agent - Quick Start Guide

**Status:** ✅ **Phase 4 Complete - Production Ready**

The Research Navigator Agent is a fully functional ReAct-style research agent that intelligently combines internal knowledge base search (RAG) with external web search (Tavily) to answer research queries.

---

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Configuration](#configuration)
- [Examples](#examples)
- [Features](#features)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Python 3.10 or higher (tested with Python 3.13.5)
- OpenAI API key
- Tavily API key (for web search)

### Step 1: Clone and Navigate

```bash
cd research-navigator-agent
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
```

### Step 3: Install Dependencies

```bash
# Install the package and all dependencies
pip install -e .
```

This will install:
- LangGraph 0.2+ (agent orchestration)
- LangChain 0.3+ (RAG components)
- OpenAI SDK (LLM and embeddings)
- FAISS (vector search)
- Tavily (web search)
- Typer + Rich (CLI)
- And all other dependencies

### Step 4: Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

Required in `.env`:
```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
TAVILY_API_KEY=tvly-your-tavily-key-here

# Optional (for API proxies)
OPENAI_BASE_URL=https://api.openai.com/v1

# Model configuration
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
```

**Important**: If using custom models, ensure your API endpoint supports them. For standard OpenAI API, use `gpt-4o`, `gpt-4-turbo`, or `gpt-3.5-turbo`.

### Step 5: Verify Installation

```bash
# Run quick smoke test (no API calls)
python test_phase4_quick.py
```

You should see:
```
✅ All Phase 4 quick tests PASSED!
```

---

## Basic Usage

### Running the Agent

**Basic syntax:**
```bash
venv/bin/research-nav main "YOUR QUERY HERE" [OPTIONS]
```

**Note**: If you've activated the virtual environment with `source venv/bin/activate`, you can omit `venv/bin/` and just use `research-nav main "query"`.

### Simple Queries

```bash
# Web search only (no knowledge base)
venv/bin/research-nav main "What are the latest developments in quantum computing?"

# With knowledge base (RAG + Web)
venv/bin/research-nav main "What is quantum computing?" \
  --kb ./knowledge/sample_docs

# Limit reasoning steps
venv/bin/research-nav main "Compare quantum and classical computing" \
  --kb ./knowledge/sample_docs \
  --max-steps 5

# Save output to file
venv/bin/research-nav main "Quantum computing applications" \
  --kb ./knowledge \
  --output research_brief.md
```

### With Verbose Logging

```bash
# See detailed API calls, timing, and token usage
venv/bin/research-nav main "What is quantum computing?" \
  --kb ./knowledge/sample_docs \
  --verbose
```

This shows:
- LLM reasoning decisions
- API call timing
- Token usage
- Search results
- Complete reasoning trace

---

## Advanced Usage

### Using Your Own Knowledge Base

1. **Create a directory** with your documents:
```bash
mkdir my_knowledge_base
```

2. **Add documents** (supports .txt, .md, .pdf):
```bash
cp my_research_papers/*.pdf my_knowledge_base/
cp my_notes/*.md my_knowledge_base/
```

3. **Run the agent**:
```bash
venv/bin/research-nav main "Your research question" \
  --kb ./my_knowledge_base
```

The agent will:
- Load all documents
- Create FAISS vector embeddings
- Save to `data/vectorstore/` for fast loading next time
- Search using semantic similarity

### Configuration Commands

```bash
# Check current configuration
venv/bin/research-nav config

# Show version information
venv/bin/research-nav version

# Validate API keys before running
venv/bin/research-nav main "test query" --check-config
```

### Adjusting LLM Parameters

Edit `.env` file:
```bash
# Use a different model
LLM_MODEL=gpt-4-turbo

# Adjust creativity (0.0 = deterministic, 1.0 = creative)
LLM_TEMPERATURE=0.7

# Adjust max response length
LLM_MAX_TOKENS=2000

# Change number of search results
TOP_K_RESULTS=5

# Maximum reasoning steps before forcing finish
MAX_STEPS=10
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT and embeddings |
| `TAVILY_API_KEY` | Yes | - | Tavily API key for web search |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | Custom API endpoint (for proxies) |
| `LLM_MODEL` | No | `gpt-4o` | Model for reasoning and synthesis |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Model for document embeddings |
| `LLM_TEMPERATURE` | No | `0.7` | Creativity level (0.0-1.0) |
| `LLM_MAX_TOKENS` | No | `2000` | Max tokens for synthesis |
| `MAX_STEPS` | No | `10` | Max reasoning steps |
| `TOP_K_RESULTS` | No | `5` | Results per search |
| `VECTORSTORE_DIR` | No | `./data/vectorstore` | Vector store location |

### Settings File

All settings are managed in `src/config/settings.py` using Pydantic Settings. You can override defaults via environment variables or `.env` file.

---

## Examples

### Example 1: Simple Factual Query

```bash
venv/bin/research-nav main "What is quantum computing?" \
  --kb ./knowledge/sample_docs
```

**Output:**
```markdown
# Research Brief: What is quantum computing?

## Summary
Quantum computing is a computing paradigm that uses quantum-mechanical
phenomena—qubits, superposition, and entanglement—to process information
differently than classical bits.

## Key Findings
• Quantum computers use qubits that can exist in superpositions of 0 and 1
• Operations performed by quantum gates (Pauli, Hadamard, CNOT)
• Fundamentally different from classical von Neumann architecture
• Limited by decoherence, error rates, and scalability challenges

## Sources
### Internal Knowledge Base
- Quantum Computing Fundamentals (quantum_computing.md)
- Classical Computing Fundamentals (classical_computing.md)

## Reasoning Trace
Step 0: Searched internal knowledge base for foundational concepts
Step 1: Retrieved 5 relevant documents about quantum computing
Step 2: Synthesized comprehensive answer from sources
```

### Example 2: Current Events Query (Web Only)

```bash
venv/bin/research-nav main "What are the latest quantum computing breakthroughs in 2024?"
```

The agent will:
1. Recognize no KB is provided
2. Route directly to web search
3. Find current articles and news
4. Synthesize findings with citations

### Example 3: Comparative Analysis (KB + Web)

```bash
venv/bin/research-nav main \
  "Compare quantum and classical computing for cryptography applications" \
  --kb ./knowledge/sample_docs \
  --max-steps 8 \
  --verbose
```

**Reasoning trace you'll see:**
```
Step 0: THOUGHT: Search internal KB for foundational comparison
        ACTION: search_internal

Step 1: THOUGHT: Good foundation, need current real-world applications
        ACTION: web_search

Step 2: THOUGHT: Have comprehensive information from both sources
        ACTION: finish
```

### Example 4: Saving Research Brief

```bash
venv/bin/research-nav main \
  "Quantum computing applications in drug discovery" \
  --kb ./knowledge \
  --output quantum_drug_discovery.md
```

Creates `quantum_drug_discovery.md` with full research brief.

---

## Features

### ✅ Completed Features (Phase 4)

**ReAct Agent Loop:**
- ✅ LLM-powered reasoning for intelligent tool selection
- ✅ Dynamic strategy adaptation based on context
- ✅ Transparent THOUGHT/ACTION/ACTION_INPUT format
- ✅ Complete reasoning trace
- ✅ Graceful error handling with fallbacks

**Internal RAG Search:**
- ✅ FAISS vector store with OpenAI embeddings
- ✅ Multi-format document loading (.txt, .md, .pdf)
- ✅ Semantic similarity search
- ✅ Vector store persistence (fast loading after first build)
- ✅ Top-k retrieval with configurable k

**External Web Search:**
- ✅ Tavily API integration
- ✅ Real-time web search
- ✅ Structured results with titles, URLs, content
- ✅ Result ranking by relevance

**LLM Synthesis:**
- ✅ Multi-source synthesis (internal + external)
- ✅ Structured markdown research briefs
- ✅ Source attribution and citations
- ✅ Reasoning trace summary
- ✅ Error recovery with fallback templates

**Infrastructure:**
- ✅ Verbose logging with API call timing
- ✅ Token usage tracking
- ✅ Custom API base URL support (for proxies)
- ✅ Pydantic Settings configuration
- ✅ Rich CLI interface with colors and formatting
- ✅ Progress indicators and status updates

### Performance Characteristics

| Metric | Typical Value |
|--------|---------------|
| Total Execution Time | 15-30 seconds |
| LLM Reasoning Calls | 3-6 per query |
| RAG Search | 0.5-2.5 seconds |
| Web Search | 5-10 seconds |
| Synthesis | 3-6 seconds |
| Tokens per Query | 5,000-8,000 |
| Cost per Query | $0.05-0.15 (GPT-4o) |

**First-time vs Subsequent:**
- First run with new KB: ~25-35 seconds (builds vector store)
- Subsequent runs: ~15-25 seconds (loads cached vector store)

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai'"

**Cause**: Packages not installed or wrong Python environment.

**Solution**:
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install the package
pip install -e .
```

### "Command not found: research-nav"

**Cause**: Either you're not using the full path or the package isn't installed.

**Solution**:

**Option 1** - Use full path (always works):
```bash
venv/bin/research-nav main "your query"
```

**Option 2** - Activate venv first:
```bash
source venv/bin/activate
research-nav main "your query"
```

**Option 3** - Reinstall package:
```bash
pip install -e .
```

### "No such command 'What is...'"

**Cause**: Forgot the `main` subcommand.

**Solution**: Always include `main` after `research-nav`:
```bash
# Wrong:
venv/bin/research-nav "query"

# Correct:
venv/bin/research-nav main "query"
```

### "Error code: 401 - Incorrect API key"

**Cause**: API keys not configured or incorrect.

**Solution**:
```bash
# Check your .env file exists
cat .env

# Verify API keys are set
venv/bin/research-nav config

# Update .env with correct keys
nano .env
```

### "Error code: 400 - Unsupported parameter: 'max_tokens'"

**Cause**: Using a model that requires `max_completion_tokens` instead of `max_tokens`.

**Solution**: This has been fixed in the latest version. Make sure you're on the latest commit:
```bash
git pull origin main
pip install -e .
```

If still seeing this error, the model name might be incorrect. Use standard OpenAI models:
```bash
# In .env, use one of:
LLM_MODEL=gpt-4o
LLM_MODEL=gpt-4-turbo
LLM_MODEL=gpt-3.5-turbo
```

### "externally-managed-environment" error

**Cause**: Trying to install system-wide on Homebrew-managed Python.

**Solution**: Always use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Slow Performance

**Possible causes and solutions:**

1. **First-time vector store build** (expected):
   - First run: ~25-35 seconds (builds embeddings)
   - Subsequent: ~15-25 seconds (loads from cache)
   - This is normal!

2. **Many documents in KB**:
   - Reduce with `TOP_K_RESULTS=3` in `.env`
   - Or use smaller knowledge base

3. **LLM being thorough**:
   - Reduce `MAX_STEPS=5` in `.env`
   - Agent will finish sooner

4. **Network latency**:
   - Use custom `OPENAI_BASE_URL` closer to you
   - Check internet connection

### Agent Searches Multiple Times

**Observation**: LLM searches the same source multiple times.

**This is normal**: The LLM is being thorough and trying different query formulations. This is expected ReAct behavior where the agent refines its understanding.

**To reduce**:
```bash
# Lower max steps
venv/bin/research-nav main "query" --max-steps 3
```

---

## Testing

### Quick Validation (No API Calls)

```bash
# Test structure without making API calls
python test_phase4_quick.py
```

Expected output:
```
✅ All Phase 4 quick tests PASSED!

Phase 4 components validated:
  ✓ LLM client initialization
  ✓ Reasoning prompt generation
  ✓ Synthesis prompt generation
  ✓ Response parsing
  ✓ Fallback handling
  ✓ Agent state initialization
```

### Full Integration Test (With API Calls)

```bash
# Test with real API calls (will cost ~$0.20 in API fees)
python test_phase4.py
```

Expected output:
```
✅ All Phase 4 tests completed successfully!

Phase 4 Features Validated:
  ✓ LLM-based reasoning for tool selection
  ✓ Dynamic internal RAG search
  ✓ Dynamic external web search
  ✓ LLM-based synthesis of final answer
  ✓ Complete reasoning trace logging
  ✓ Error handling and fallbacks
```

### Testing with Custom Knowledge Base

```bash
# Add your own documents
mkdir test_kb
echo "Your custom content here" > test_kb/doc1.md

# Test with custom KB
venv/bin/research-nav main "Query about your content" \
  --kb ./test_kb \
  --verbose
```

---

## Command Reference

### Main Commands

```bash
# Run a query
venv/bin/research-nav main "QUERY" [OPTIONS]

# Show configuration
venv/bin/research-nav config

# Show version
venv/bin/research-nav version

# Show help
venv/bin/research-nav --help
venv/bin/research-nav main --help
```

### Common Options for `main` Command

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--kb` | - | Knowledge base directory | `--kb ./knowledge` |
| `--max-steps` | - | Max reasoning steps | `--max-steps 5` |
| `--output` | `-o` | Save output file | `-o report.md` |
| `--verbose` | `-v` | Enable verbose logging | `-v` |
| `--check-config` | - | Validate configuration | `--check-config` |

---

## Next Steps

### For Users

1. **Add Your Knowledge Base**:
   - Put your documents in a directory
   - Run agent with `--kb ./your_directory`

2. **Customize Prompts**:
   - Edit `src/tools/llm_client.py` to modify ReAct prompts
   - Adjust reasoning and synthesis templates

3. **Integrate into Applications**:
   - Import `run_agent()` from `src.agent.controller`
   - Use programmatically in your Python code

### For Developers

1. **Add New Tools**:
   - See `CLAUDE.md` for extension guide
   - Add new nodes in `src/agent/nodes.py`
   - Update graph in `src/agent/graph.py`

2. **Customize Agent Behavior**:
   - Modify reasoning prompts in `llm_client.py`
   - Adjust routing logic in `graph.py`
   - Add custom tools in `src/tools/`

3. **Improve Performance**:
   - Add caching layer
   - Implement query deduplication
   - Use streaming responses

---

## Documentation

- **CLAUDE.md** - Complete architecture documentation
- **PROJECT_STATUS.md** - Project overview and status
- **PHASE4_COMPLETE.md** - Phase 4 detailed documentation
- **TEST_RESULTS.md** - Test results and validation
- **README.md** - Project README (to be created)

---

## Support

**Issues**: https://github.com/hunteryang1988/research-navigator-agent/issues

**Documentation**: See `CLAUDE.md` for complete architecture details

---

**Version**: 1.0 (Phase 4 Complete)
**Status**: ✅ Production Ready
**Last Updated**: 2025-11-29
