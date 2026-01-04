# RAG Learning Project

A hands-on learning project to build a Retrieval-Augmented Generation (RAG) system from scratch.

## What is RAG?

RAG combines retrieval (finding relevant information) with generation (using an LLM to create responses). It allows LLMs to answer questions based on specific data sources rather than just their training data.

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | **Complete** | Data Ingestion (Hacker News API) |
| Phase 2 | **Complete** | Embedding & Vector Storage |
| Phase 3 | **Complete** | Query & Retrieval (Hybrid Search) |
| Phase 4 | Pending | LLM Integration |
| Phase 5 | Pending | User Interface |
| Phase 6 | Pending | Enhancements |

## Quick Start

```bash
# Install dependencies
poetry install

# Copy environment template
cp .env.example .env

# Option A: Step by step
poetry run rag-fetch --limit 100   # Fetch articles
poetry run rag-process             # Build index

# Option B: Combined (same as Option A)
poetry run rag-ingest              # Fetch + build index

# Query the system
poetry run rag-query
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `rag-fetch` | Fetch articles from Hacker News API → `data/raw/articles.json` |
| `rag-process` | Build search index from articles (chunk → embed → store) |
| `rag-ingest` | Shortcut: runs `rag-fetch` + `rag-process` |
| `rag-query` | Interactive query interface with hybrid search |

## Architecture

```
[rag-fetch]                    [rag-process]
Hacker News API → Articles → Chunking → Embedding → Vector DB + BM25 Index
                  (JSON)                                    ↓
                                                      [rag-query]
User Query → Query Embedding → Hybrid Search (BM25 + Vector) → Results
                                                               ↓
                                                         [Phase 4]
                                                      LLM → Response
```

## Project Structure

```
rag-learning-project/
├── README.md
├── CLAUDE.md              # Guidance for Claude Code
├── SETUP_GUIDE.md         # Development environment setup
├── pyproject.toml         # Poetry dependencies and scripts
├── docs/
│   └── IMPLEMENTATION_LOG.md
├── src/
│   ├── ingestion/         # rag-fetch: HN client, models
│   ├── indexing/          # rag-process: chunking, embedding, storage
│   ├── embeddings/        # Embedding generation
│   ├── vector_db/         # ChromaDB operations
│   ├── retrieval/         # rag-query: hybrid search, BM25
│   └── llm/               # LLM integration (Phase 4)
├── tests/                 # 117 passing tests
└── data/                  # Generated (gitignored)
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required for Phase 4 (LLM integration)
ANTHROPIC_API_KEY=your_key_here

# Embedding model (default works without API key)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Retrieval settings
SIMILARITY_THRESHOLD=0.3
RETRIEVAL_K=5
MAX_CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

---

## Implementation Details

### Phase 1: Data Ingestion [COMPLETE]

**Data Source**: Hacker News API
- `src/ingestion/hn_client.py` - Fetches Ask HN, Show HN posts
- `src/ingestion/fetch.py` → `rag-fetch` CLI
- Retry logic with exponential backoff
- Saves to `data/raw/articles.json`

**Data Models**: `src/ingestion/models.py`
- `Article` - Raw article with JSON serialization
- `Document` - Processed document
- `Chunk` - Text chunk with metadata

**Preprocessing**: `src/ingestion/preprocessor.py`
- Sentence-aware chunking (500 chars, 50 overlap)

### Phase 2: Embedding & Storage [COMPLETE]

**Embeddings**: `src/embeddings/embedder.py`
- Sentence-Transformers `all-MiniLM-L6-v2` (local, free)
- Batch processing with progress bar

**Vector Database**: `src/vector_db/store.py`
- ChromaDB with cosine similarity
- Persistent storage in `data/chroma_db/`

### Phase 3: Query & Retrieval [COMPLETE]

**Hybrid Search**: `src/retrieval/hybrid_retriever.py`
- Vector similarity search
- BM25 keyword search: `src/retrieval/bm25_index.py`
- Reciprocal Rank Fusion for score combination

**CLI**: `src/retrieval/main.py` → `rag-query`
- Interactive query loop
- Options: `k=N`, `t=N` (threshold), `mode=hybrid/vector/bm25`

### Phase 4: LLM Integration [PENDING]

- [ ] Anthropic Claude API client
- [ ] RAG prompt template with context injection
- [ ] Citation formatting
- [ ] Response streaming

### Phase 5: User Interface [PENDING]

- [ ] Rich CLI formatting
- [ ] Web interface (Streamlit/Gradio)

### Phase 6: Enhancements [PENDING]

- [ ] Evaluation metrics (Precision@k, recall)
- [ ] Conversational RAG
- [ ] Embedding caching

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.9+ |
| Package Manager | Poetry |
| Data Source | Hacker News Firebase API |
| Embeddings | Sentence-Transformers |
| Vector DB | ChromaDB |
| Keyword Search | BM25 (rank-bm25) |
| LLM | Anthropic Claude (Phase 4) |

## Development

```bash
# Run tests
poetry run pytest -v

# Query with options
poetry run rag-query
# Commands: k=N (results), t=N (threshold), mode=hybrid/vector/bm25
```

## Resources

- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Environment setup
- [docs/IMPLEMENTATION_LOG.md](./docs/IMPLEMENTATION_LOG.md) - Detailed notes
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Anthropic Claude](https://docs.anthropic.com/)
