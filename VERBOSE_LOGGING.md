# Verbose Logging Guide

## Overview

The Research Navigator Agent now includes comprehensive verbose logging for all OpenAI API calls. This helps with debugging, cost tracking, and understanding the agent's execution flow.

## What Gets Logged

### 1. **Embedding Generation** (Active in Phase 2)
- Model name and configuration
- Number of texts being embedded
- Total character count
- Estimated token count
- Estimated API cost
- Request/response timing
- Success/failure status

### 2. **Vector Store Operations**
- Build/Load/Save operations
- Number of documents and chunks
- Storage paths
- Index size

### 3. **Vector Search Queries**
- Query text
- Top-K parameter
- Vectorstore size
- Search results with similarity scores
- Result previews

### 4. **LLM Calls** (Will be active in Phase 4)
- Model and parameters (temperature, max_tokens)
- Prompt content (preview)
- Response content (preview)
- Token usage (prompt, completion, total)
- Request/response timing

## How to Enable

### Method 1: CLI Flag (Recommended)

```bash
# Basic usage with verbose logging
venv/bin/research-nav main "Your query" --verbose

# With knowledge base
venv/bin/research-nav main "Compare quantum computing" \
  --kb ./knowledge/sample_docs \
  --verbose

# Short form
venv/bin/research-nav main "Your query" -v
```

### Method 2: Programmatic

```python
from src.tools.api_logger import set_verbose
from src.agent.controller import run_agent

# Enable verbose mode
set_verbose(True)

# Run agent
run_agent(
    query="What is quantum computing?",
    kb_path="./knowledge/sample_docs",
    max_steps=5
)
```

### Method 3: Test Scripts

```bash
# Test verbose logging
venv/bin/python test_verbose.py
```

## Example Output

### Embedding API Call

```
================================================================================
🔌 API CALL START
================================================================================
  API                 OpenAI Embeddings
  Operation           Generate document embeddings
  Model               text-embedding-3-small
  Time                2025-11-28 20:13:49
  Num Documents       7
  Estimated Tokens    1346
Sending request...
```

### Embedding Details

```
📊 EMBEDDING CALL DETAILS
  Model               text-embedding-3-small
  Number of Texts     7
  Total Characters    5,385
  Estimated Tokens    1,346
  Estimated Cost      $0.000027
```

### API Call Result

```
================================================================================
✅ API CALL SUCCESS
================================================================================
  Duration           1.74s
  Vectors Created    7
  Vectorstore Type   FAISS
================================================================================
```

### Search Query

```
🔍 VECTOR SEARCH QUERY
  Query              What is quantum computing?
  Top K              5
  Vectorstore Size   7 vectors
```

### Search Results

```
📋 SEARCH RESULTS:
Found 5 results

Result 1 (score: 0.1234):
Quantum computing is a revolutionary computing paradigm that leverages
principles of quantum mechanics...

Result 2 (score: 0.2456):
Unlike classical computers that use bits (0 or 1), quantum computers use
quantum bits or qubits...
```

## Logged Information by Component

### API Call Logger (`src/tools/api_logger.py`)

The `APICallLogger` context manager tracks:
- API name and operation
- Model being used
- Start/end timestamps
- Duration in seconds
- Request parameters
- Response metadata
- Errors with details

Usage in code:
```python
with APICallLogger(
    api_name="OpenAI Embeddings",
    operation="Generate embeddings",
    model="text-embedding-3-small",
    num_documents=7,
) as logger:
    # API call here
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Log results
    logger.log_result(
        vectors_created=len(documents),
        vectorstore_type="FAISS",
    )
```

### Specialized Logging Functions

**Embeddings:**
```python
log_embedding_call(
    model="text-embedding-3-small",
    num_texts=7,
    total_chars=5385,
    estimated_tokens=1346,
)
```

**Vector Store:**
```python
log_vectorstore_operation(
    operation="BUILD",
    num_documents=2,
    num_chunks=7,
    vectorstore_path="./data/vectorstore",
)
```

**Search:**
```python
log_search_query(
    query="What is quantum computing?",
    top_k=5,
    vectorstore_size=7,
)

log_search_results(
    results=chunks,
    scores=[0.123, 0.245, 0.367],
)
```

**LLM (Phase 4):**
```python
log_llm_call(
    model="gpt-5-mini",
    prompt="Your prompt here",
    max_tokens=4096,
    temperature=0.7,
)

log_llm_response(
    response_text="Generated response",
    prompt_tokens=150,
    completion_tokens=300,
    total_tokens=450,
)
```

## Integration Points

### Current (Phase 2)

1. **`src/tools/rag_loader.py`**
   - Lines 163-168: Embedding call details
   - Lines 179-190: API call tracking
   - Lines 195-200: Vectorstore operation logging
   - Lines 256-261: Load operation logging

2. **`src/tools/rag_search.py`**
   - Lines 96-100: Search query logging
   - Lines 107-131: Query embedding tracking
   - Lines 139: Search results logging

### Future (Phase 4)

Will add logging to:
- `src/agent/nodes.py` - `reason_node()` LLM calls
- `src/agent/nodes.py` - `finish_node()` LLM calls

## Cost Tracking

The logger estimates costs based on current OpenAI pricing:

- **text-embedding-3-small**: $0.00002 per 1K tokens
- **gpt-4o**: ~$0.0025 per 1K prompt tokens, ~$0.01 per 1K completion tokens
- **gpt-5-mini**: TBD (if model exists)

Example:
```
Estimated Tokens    1,346
Estimated Cost      $0.000027
```

## Performance Monitoring

Every API call shows duration:
```
Duration    1.74s
```

This helps identify:
- Slow API responses
- Network issues
- Rate limiting
- API quota problems

## Error Tracking

Failed API calls show detailed errors:
```
================================================================================
❌ API CALL FAILED
Error: Error code: 401 - {'error': {'message': 'Incorrect API key...'}}
================================================================================
  Duration    1.74s
================================================================================
```

Common errors logged:
- **401**: Invalid API key
- **429**: Rate limit or quota exceeded
- **500**: OpenAI server error
- Network timeouts
- Connection errors

## Debugging Tips

### 1. Track Token Usage

Monitor token consumption to optimize:
```bash
research-nav main "query" --kb ./knowledge --verbose | grep "Tokens"
```

### 2. Measure Performance

Check API response times:
```bash
research-nav main "query" --kb ./knowledge --verbose | grep "Duration"
```

### 3. Verify Embeddings

See what's being embedded:
```bash
research-nav main "query" --kb ./knowledge --verbose | grep -A 10 "EMBEDDING"
```

### 4. Inspect Search Results

Review retrieval quality:
```bash
research-nav main "query" --kb ./knowledge --verbose | grep -A 20 "SEARCH RESULTS"
```

## Configuration

Verbose mode is controlled by a global flag in `api_logger.py`:

```python
_verbose_mode = False  # Default: off

def set_verbose(enabled: bool):
    """Enable or disable verbose logging."""
    global _verbose_mode
    _verbose_mode = enabled
```

All logging functions check this flag:
```python
if not _verbose_mode:
    return  # Skip logging
```

## Files Added/Modified

### New Files
- `src/tools/api_logger.py` (370 lines) - Complete logging infrastructure

### Modified Files
- `src/tools/rag_loader.py` - Added embedding and vectorstore logging
- `src/tools/rag_search.py` - Added search logging
- `src/cli/main.py` - Added `--verbose` / `-v` flag
- `test_verbose.py` - Test script for verbose mode

## Testing

Run the verbose logging test:

```bash
# Test with sample documents
venv/bin/python test_verbose.py

# Test via CLI
venv/bin/research-nav main "Test query" --kb ./knowledge/sample_docs --verbose

# Compare verbose vs normal
venv/bin/research-nav main "Test query" --kb ./knowledge     # Normal
venv/bin/research-nav main "Test query" --kb ./knowledge -v  # Verbose
```

## Production Recommendations

### Development
✅ **Use verbose mode** for:
- Debugging API issues
- Optimizing token usage
- Understanding agent behavior
- Tracking costs

### Production
❌ **Disable verbose mode** because:
- Reduces console clutter
- Improves performance (no formatting overhead)
- Cleaner logs for users
- Still logs errors automatically

### CI/CD
- Enable verbose in integration tests
- Use for performance benchmarking
- Track token usage trends

---

**Status:** ✅ Fully implemented and tested
**Phase:** 2 (Active for embeddings)
**Future:** Will add LLM call logging in Phase 4
