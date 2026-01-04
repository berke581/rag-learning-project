# Development Environment Setup Guide

Complete guide to set up your development environment for the RAG Learning Project.

## Prerequisites

- **Python 3.9+** installed
- **Poetry** package manager ([installation guide](https://python-poetry.org/docs/#installation))

## Quick Setup

```bash
# Clone or navigate to project
cd rag-learning-project

# Install dependencies
poetry install

# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional for Phases 1-3)
# ANTHROPIC_API_KEY is only needed for Phase 4

# Verify installation
poetry run pytest -v
```

## Step-by-Step Setup

### Step 1: Install Poetry

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Step 2: Install Dependencies

```bash
poetry install
```

This installs:
- `requests` - HTTP client for Hacker News API
- `sentence-transformers` - Local embedding model
- `chromadb` - Vector database
- `rank-bm25` - BM25 keyword search
- `python-dotenv` - Environment variable loading
- `pytest` - Testing framework

### Step 3: Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` as needed:
```bash
# LLM API Key (only needed for Phase 4)
ANTHROPIC_API_KEY=your_key_here

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
MODEL_CACHE_DIR=./data/models

# Vector Database
VECTOR_DB_PATH=./data/chroma_db
VECTOR_DB_COLLECTION=rag_documents

# Chunking
MAX_CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Retrieval
SIMILARITY_THRESHOLD=0.3
RETRIEVAL_K=5
```

### Step 4: Verify Installation

```bash
# Run tests
poetry run pytest -v

# Should see: 117 passed
```

## Running the Pipeline

```bash
# Fetch articles from Hacker News
poetry run rag-fetch --limit 50

# Build search index
poetry run rag-process

# Query the system
poetry run rag-query
```

Or run the complete pipeline:
```bash
poetry run rag-ingest
```

## Project Structure

```
rag-learning-project/
├── .env                    # Environment variables (DO NOT COMMIT)
├── .env.example            # Template for .env
├── .gitignore
├── pyproject.toml          # Poetry dependencies
├── poetry.lock             # Locked dependency versions
├── src/
│   ├── ingestion/          # rag-fetch
│   ├── indexing/           # rag-process
│   ├── embeddings/         # Embedding generation
│   ├── vector_db/          # ChromaDB storage
│   ├── retrieval/          # rag-query
│   └── llm/                # Phase 4
├── tests/
├── data/                   # Generated (gitignored)
│   ├── raw/articles.json
│   ├── chroma_db/
│   └── bm25_index.pkl
└── docs/
```

## Getting API Keys

### Anthropic Claude API (Phase 4)
1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Add to `.env` as `ANTHROPIC_API_KEY`

**Note:** API key is only needed for Phase 4 (LLM integration). Phases 1-3 work without any API key.

## Troubleshooting

### Poetry not found
Add Poetry to your PATH:
- Windows: `%APPDATA%\Python\Scripts`
- macOS/Linux: `$HOME/.local/bin`

### Import errors
```bash
# Ensure you're using poetry's virtual environment
poetry shell
# Or prefix commands with: poetry run
```

### ChromaDB issues
```bash
# Delete and recreate the database
rm -rf data/chroma_db
poetry run rag-process
```

### First run is slow
The embedding model downloads on first use (~90MB). Subsequent runs use the cached model from `data/models/`.

## Development Workflow

```bash
# Activate virtual environment
poetry shell

# Run tests
pytest -v

# Run specific test file
pytest tests/test_embeddings.py -v

# Query with custom settings
python -m src.retrieval.main
# Then: k=10 t=0.2 mode=bm25
```

## Next Steps

1. Run `poetry run rag-fetch --limit 50` to fetch sample articles
2. Run `poetry run rag-process` to build the index
3. Run `poetry run rag-query` to search
4. Read ROADMAP.md for implementation details
