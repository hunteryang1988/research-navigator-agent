# Research Navigator Agent - Architecture Documentation

## Overview

This project implements a ReAct (Reasoning + Acting) style research agent using LangGraph. The agent can dynamically choose between internal knowledge base search (RAG) and external web search (Tavily) to answer research queries.

## Architecture Components

### 1. Agent State Management

**Location:** `src/agent/schema.py`

The `AgentState` is a TypedDict that flows through the LangGraph state machine:

```python
class AgentState(TypedDict):
    query: str                      # Original user query
    history: list[str]              # Conversation history (optional)
    scratchpad: list[dict]          # ReAct reasoning trace
    tool_calls: list[dict]          # Record of all tool invocations
    internal_context: list[str]     # RAG search results
    external_context: list[dict]    # Web search results
    step: int                       # Current step counter
    max_steps: int                  # Maximum allowed steps
    final_answer: str               # Generated research brief
```

### 2. LangGraph State Machine

**Location:** `src/agent/graph.py`

The agent follows this graph structure:

```
START
  ↓
reason_node (LLM decides next action)
  ↓
  ├─→ act_internal_node (RAG search) ──┐
  ├─→ act_external_node (Web search) ──┤
  └─→ finish_node (Generate answer) ───→ END
       ↑
       └───────────────────────────────┘
       (loop back if step < max_steps)
```

**Conditional Routing Logic:**
- If LLM decides `search_internal` → route to `act_internal_node`
- If LLM decides `web_search` → route to `act_external_node`
- If LLM decides `finish` OR `step >= max_steps` → route to `finish_node`

### 3. Nodes Implementation

**Location:** `src/agent/nodes.py`

#### `reason_node(state: AgentState) -> AgentState`
- Takes current state (query, scratchpad, accumulated context)
- Calls GPT-4o with ReAct-style prompt
- LLM outputs:
  - `thought`: reasoning about what to do next
  - `action`: one of `search_internal`, `web_search`, or `finish`
  - `action_input`: the query/parameters for the chosen action
- Appends to `scratchpad`
- Returns updated state

#### `act_internal_node(state: AgentState) -> AgentState`
- Calls `tools/rag_search.search_internal()`
- Appends results to `state.internal_context`
- Records tool call in `state.tool_calls`
- Increments `state.step`
- Returns updated state

#### `act_external_node(state: AgentState) -> AgentState`
- Calls `tools/tavily_tool.web_search()`
- Appends results to `state.external_context`
- Records tool call in `state.tool_calls`
- Increments `state.step`
- Returns updated state

#### `finish_node(state: AgentState) -> AgentState`
- Takes all accumulated context (internal + external)
- Calls GPT-4o to synthesize a structured research brief
- Output format:
  ```markdown
  # Research Brief: [Query]

  ## Summary
  [High-level overview]

  ## Key Findings
  1. [Finding from RAG/Web]
  2. [Finding from RAG/Web]
  ...

  ## Sources
  - Internal: [List of KB documents used]
  - External: [List of web URLs]

  ## Reasoning Trace
  [Summary of ReAct steps taken]
  ```
- Sets `state.final_answer`
- Returns final state

### 4. Tools

#### RAG Search (`tools/rag_search.py`)
```python
def search_internal(query: str, top_k: int = 5) -> list[str]:
    """
    Searches the internal knowledge base using FAISS vector similarity.
    Returns top_k most relevant document chunks.
    """
```

**Dependencies:**
- Vector store loaded from `VECTORSTORE_DIR`
- Uses OpenAI `text-embedding-3-small` for query embedding
- FAISS for similarity search

#### Web Search (`tools/tavily_tool.py`)
```python
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Performs web search using Tavily API.
    Returns list of {title, url, content} dicts.
    """
```

**Dependencies:**
- Tavily API key from environment
- Returns structured web results with snippets

#### RAG Loader (`tools/rag_loader.py`)
```python
def load_documents(kb_path: str) -> list[Document]:
    """Load documents from directory using LangChain loaders."""

def build_vectorstore(docs: list[Document], output_dir: str):
    """Build FAISS index with OpenAI embeddings."""

def get_or_create_vectorstore(kb_path: str) -> VectorStore:
    """Load existing or create new vector store."""
```

### 5. Configuration

**Location:** `src/config/settings.py`

Uses Pydantic Settings to load from `.env`:

```python
class Settings(BaseSettings):
    openai_api_key: str
    tavily_api_key: str
    vectorstore_dir: Path
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    max_steps: int = 10
    top_k_results: int = 5

    class Config:
        env_file = ".env"
```

### 6. CLI

**Location:** `src/cli/main.py`

Typer-based CLI with rich output:

```bash
research-nav "Your query here" \
  --kb ./knowledge/sample_docs \
  --max-steps 8 \
  --output report.md
```

Internally calls `agent.controller.run_agent()`.

## Data Flow Example

1. User runs: `research-nav "Compare quantum and classical computing" --kb ./knowledge --max-steps 5`

2. Controller initializes state:
   ```python
   state = {
       "query": "Compare quantum and classical computing",
       "scratchpad": [],
       "tool_calls": [],
       "internal_context": [],
       "external_context": [],
       "step": 0,
       "max_steps": 5,
   }
   ```

3. Step 1: `reason_node`
   - LLM thinks: "I should first check internal knowledge base"
   - Action: `search_internal`
   - Routes to `act_internal_node`

4. Step 2: `act_internal_node`
   - Calls RAG search
   - Finds 3 relevant docs
   - Updates `internal_context`, increments `step`
   - Routes back to `reason_node`

5. Step 3: `reason_node`
   - LLM thinks: "Internal docs are good but I need current info"
   - Action: `web_search`
   - Routes to `act_external_node`

6. Step 4: `act_external_node`
   - Calls Tavily API
   - Gets 5 web results
   - Updates `external_context`, increments `step`
   - Routes back to `reason_node`

7. Step 5: `reason_node`
   - LLM thinks: "I have enough information"
   - Action: `finish`
   - Routes to `finish_node`

8. `finish_node`
   - Synthesizes research brief from both contexts
   - Returns final answer

## Technology Stack

- **LangGraph 0.2+**: State machine orchestration
- **LangChain 0.3+**: RAG components (loaders, vector stores, retrievers)
- **OpenAI GPT-4o**: Primary reasoning LLM
- **OpenAI text-embedding-3-small**: Document embeddings
- **FAISS**: Vector similarity search
- **Tavily API**: Web search
- **Typer + Rich**: CLI interface
- **Pydantic Settings**: Configuration management

## Extensibility

To add a new tool:

1. **Create tool function** in `src/tools/new_tool.py`:
   ```python
   def my_new_tool(input: str) -> dict:
       # Implementation
       return {"result": "..."}
   ```

2. **Add node** in `src/agent/nodes.py`:
   ```python
   def act_newtool_node(state: AgentState) -> AgentState:
       result = my_new_tool(state.scratchpad[-1]["action_input"])
       state["tool_calls"].append({"tool": "my_new_tool", "result": result})
       state["step"] += 1
       return state
   ```

3. **Update graph** in `src/agent/graph.py`:
   ```python
   graph.add_node("act_newtool", act_newtool_node)
   graph.add_conditional_edges("reason", route_action, {
       "search_internal": "act_internal",
       "web_search": "act_external",
       "my_new_tool": "act_newtool",  # Add this
       "finish": "finish"
   })
   graph.add_edge("act_newtool", "reason")
   ```

4. **Update reasoning prompt** to include new tool in available actions.

## Development Phases

See README.md for detailed phase-by-phase implementation plan.

---

**Last Updated:** 2025-11-26
**Author:** Research Navigator Team
