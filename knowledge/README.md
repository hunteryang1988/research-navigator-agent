# Knowledge Base Management

This directory contains the internal knowledge base for the Research Navigator Agent. Documents placed here can be indexed and searched using RAG (Retrieval-Augmented Generation).

## Directory Structure

```
knowledge/
├── README.md           # This file
└── sample_docs/        # Sample documents for testing
    ├── quantum_computing.md
    └── classical_computing.md
```

## Adding Your Own Documents

### Supported Formats

The RAG loader supports the following document formats:

- **Text files**: `.txt`, `.md`
- **PDF files**: `.pdf` (requires `pypdf` package)
- **Word documents**: `.docx` (requires `python-docx` package)
- **CSV files**: `.csv`
- **JSON files**: `.json`

### Steps to Add Documents

1. **Place documents in this directory or subdirectories:**

   ```bash
   cp your-document.pdf knowledge/
   # or
   cp -r your-docs-folder/ knowledge/my-docs/
   ```

2. **Build/update the vector store:**

   The vector store is automatically built when you run the agent with the `--kb` flag pointing to a directory:

   ```bash
   research-nav "Your query" --kb ./knowledge
   ```

   The first time you run this, it will:
   - Scan all documents in the directory
   - Split them into chunks
   - Generate embeddings using OpenAI's `text-embedding-3-small`
   - Build a FAISS index
   - Save the index to `data/vectorstore/`

3. **Subsequent runs:**

   Future runs will load the existing vector store unless you force a rebuild.

## Vector Store Location

By default, the vector store is saved to:

```
data/vectorstore/
├── index.faiss      # FAISS index file
└── docstore.pkl     # Document metadata
```

This directory is gitignored, so you'll need to rebuild the index on different machines.

## Rebuilding the Vector Store

To force a rebuild of the vector store (useful when adding new documents):

```bash
# Option 1: Delete the existing vector store
rm -rf data/vectorstore/

# Option 2: Use the rebuild flag (if implemented)
research-nav "query" --kb ./knowledge --rebuild
```

## Document Chunking Strategy

Documents are split into chunks for better retrieval:

- **Chunk size**: 1000 characters (configurable)
- **Chunk overlap**: 200 characters (to preserve context)
- **Splitter**: Recursive character text splitter (respects paragraphs, sentences)

## Best Practices

### 1. Organize by Topic

```
knowledge/
├── quantum/
│   ├── basics.md
│   └── algorithms.md
├── ai/
│   ├── machine-learning.md
│   └── neural-networks.md
└── databases/
    └── sql-guide.md
```

### 2. Use Descriptive Filenames

Good: `quantum-entanglement-explained.md`
Bad: `doc1.md`

### 3. Include Metadata in Documents

Add titles, headings, and context to help retrieval:

```markdown
# Topic: Quantum Entanglement
# Date: 2024-01-15
# Author: Research Team

## Introduction
...
```

### 4. Keep Documents Focused

Smaller, focused documents often retrieve better than large, multi-topic files.

### 5. Test Your Knowledge Base

After adding documents, run test queries to verify they're being retrieved:

```bash
research-nav "What does this document say about X?" --kb ./knowledge --max-steps 3
```

## Checking What's Indexed

To see what documents are in your vector store, you can inspect the metadata:

```python
from src.tools.rag_loader import get_or_create_vectorstore

vectorstore = get_or_create_vectorstore("./knowledge")
print(f"Total chunks: {vectorstore.index.ntotal}")
```

## Troubleshooting

### "No relevant documents found"

- Check that documents are in the correct directory
- Verify the vector store was built (`data/vectorstore/` should exist)
- Try rebuilding the index
- Use more specific queries

### Large documents taking too long

- Split large PDFs into smaller sections
- Reduce chunk size in configuration
- Consider preprocessing documents

### Embedding API errors

- Verify `OPENAI_API_KEY` is set in `.env`
- Check API quota limits
- Ensure network connectivity

## Configuration

Edit `src/config/settings.py` or `.env` to customize:

```env
VECTORSTORE_DIR=./data/vectorstore
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
TOP_K_RESULTS=5
```

## Advanced: Programmatic Index Management

For advanced users who want to manage the index programmatically:

```python
from src.tools.rag_loader import load_documents, build_vectorstore

# Load documents from a directory
docs = load_documents("./knowledge")

# Build a custom vector store
build_vectorstore(docs, output_dir="./data/custom_vectorstore")
```

---

For more details on the RAG implementation, see `CLAUDE.md`.
