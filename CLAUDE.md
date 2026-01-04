# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a learning project for building a RAG (Retrieval-Augmented Generation) system. The system fetches articles from Hacker News (Ask HN, Show HN posts), generates embeddings, stores them in a vector database, and enables hybrid search (BM25 + vector) with LLM-augmented responses.

## Development Workflow

The project follows a phased approach (see README.md for status):
1. Phase 1: Data ingestion from Hacker News API [COMPLETE]
2. Phase 2: Embedding generation and vector storage [COMPLETE]
3. Phase 3: Query processing and hybrid retrieval [COMPLETE]
4. Phase 4: LLM integration [PENDING]
5. Phase 5: User interface [PENDING]
6. Phase 6: Enhancements [PENDING]

## Key Architectural Decisions

### Data Flow
```
[rag-fetch]                    [rag-process]
Hacker News API → Articles → Chunking → Embedding → Vector DB + BM25 Index
                  (JSON)                                    ↓
                                                      [rag-query]
User Query → Query Embedding → Hybrid Search (BM25 + Vector) → LLM → Response
```

### CLI Commands

| Command | Module | Purpose |
|---------|--------|---------|
| `rag-fetch` | `src/ingestion/` | Fetch articles from HN, save to `data/raw/articles.json` |
| `rag-process` | `src/indexing/` | Build search index (chunk → embed → store → BM25) |
| `rag-query` | `src/retrieval/` | Query the RAG system with hybrid search |
| `rag-ingest` | `src/ingestion/` | Convenience: runs fetch + process together |

### Component Separation
- **Ingestion layer** (`src/ingestion/`): Fetches articles from Hacker News API, saves to JSON
- **Indexing layer** (`src/indexing/`): Loads articles, chunks, embeds, stores in vector DB, builds BM25 index
- **Embedding layer** (`src/embeddings/`): Manages model loading, batch processing
- **Storage layer** (`src/vector_db/`): ChromaDB vector database operations
- **Retrieval layer** (`src/retrieval/`): Hybrid search (BM25 + vector), re-ranking, filtering
- **LLM layer** (`src/llm/`): Prompt construction, API calls, response formatting

### Design Principles
- Each phase should be independently testable
- Use dependency injection for swappable components (e.g., different embedding models)
- Cache embeddings to avoid redundant API calls
- Maintain metadata alongside vectors for filtering and citation

## Environment Setup

Required environment variables (create `.env` file):
```
ANTHROPIC_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here

# Optional
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./data/chroma_db
```

## Common Patterns

### Embedding Generation
Always use the same embedding model for both document embedding and query embedding. Dimension mismatch will break similarity search.

### Chunk Size Strategy
- Small chunks (200-300 tokens): Better precision, may lack context
- Large chunks (800-1000 tokens): Better context, may dilute relevance
- Recommended: 400-600 tokens with 50-100 token overlap

### Retrieval Configuration
- `k` (number of results): Start with 3-5
- Similarity threshold: 0.7+ for cosine similarity
- Always include metadata in retrieval for citations

### Prompt Structure for RAG
```
Context: [Retrieved chunks with sources]

User Question: [Original query]

Instructions: Answer based only on the provided context. Cite sources using [Source N] notation. If the context doesn't contain relevant information, say so clearly.
```

## Testing Approach

- Unit tests: Individual components (embedding, chunking, retrieval)
- Integration tests: Full pipeline from query to response
- Evaluation: Track retrieval quality using test queries with known good results

## Tech Stack Flexibility

The project is designed to work with multiple implementations:
- **Embeddings**: OpenAI, Sentence-Transformers, Cohere
- **Vector DB**: ChromaDB, FAISS, Pinecone, Qdrant
- **LLM**: Claude (Anthropic), GPT (OpenAI), local models via Ollama

When implementing, maintain abstraction layers so switching providers only requires changing configuration.

## Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config)

**Scopes:** `ingestion`, `indexing`, `embeddings`, `retrieval`, `vector_db`, `llm`

**Examples:**
```
feat(retrieval): add hybrid search with BM25
fix(ingestion): handle API timeout errors
docs: update README with CLI commands
refactor(embeddings): extract batch processing logic
```

## File Organization

- Place reusable utilities in the appropriate `src/` subdirectory
- Keep configuration in `.env` (never commit this file)
- Store sample data and embeddings in `data/` (gitignored):
  - `data/raw/articles.json` - Fetched articles from rag-fetch
  - `data/chroma_db/` - Vector database
  - `data/bm25_index.pkl` - BM25 index
- Use `notebooks/` for experimentation and prototyping
- Write documentation in `docs/` for implementation details
