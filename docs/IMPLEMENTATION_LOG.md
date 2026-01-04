# Implementation Log

This document tracks what has been created and why, serving as a reference for understanding the project structure.

## Project Initialization - 2025-12-30

### What Was Created

#### 1. Project Structure
Created a complete directory structure for a RAG learning project:

```
rag-learning-project/
├── src/
│   ├── ingestion/      # API fetching and data processing
│   ├── embeddings/     # Embedding generation logic
│   ├── vector_db/      # Vector database operations
│   ├── retrieval/      # Search and ranking
│   └── llm/            # LLM integration
├── tests/              # Unit and integration tests
├── data/               # For cached data (gitignored)
├── notebooks/          # Jupyter notebooks for experimentation
└── docs/               # Additional documentation
```

**Why**: This structure separates concerns by component, making it easy to develop and test each phase independently. The modular approach allows swapping implementations (e.g., different embedding models or vector databases) without affecting other components.

#### 2. Documentation Files

**ROADMAP.md**
- **Purpose**: Complete step-by-step guide for building the RAG system
- **Content**: 6 phases from data ingestion to production enhancements
- **Why**: Provides a clear learning path with specific tasks, technology options, and decision points at each phase

**README.md**
- **Purpose**: Project overview and quick start guide
- **Content**: Project goals, directory structure, code examples in Python and Node.js
- **Why**: Serves as the entry point for understanding what the project does and how to get started quickly

**SETUP_GUIDE.md**
- **Purpose**: Detailed environment setup instructions
- **Content**: Step-by-step setup for both Python and Node.js, dependency installation, API key configuration, troubleshooting
- **Why**: Removes setup friction, provides clear instructions for both tech stacks, includes verification steps

**CLAUDE.md**
- **Purpose**: Guidance for Claude Code when working in this repository
- **Content**: Architectural decisions, common patterns, design principles, environment configuration
- **Why**: Helps AI assistants understand the project structure and maintain consistency when helping with development

**.env.example**
- **Purpose**: Template for environment variables
- **Content**: All required and optional environment variables with descriptions
- **Why**: Shows developers exactly what configuration is needed without exposing actual credentials

**.gitignore**
- **Purpose**: Prevent committing sensitive or generated files
- **Content**: Patterns for API keys, dependencies, data files, IDE files, OS files
- **Why**: Protects against accidentally committing secrets or bloating the repository

**IMPLEMENTATION_LOG.md** (this file)
- **Purpose**: Track what was created and why
- **Content**: Detailed documentation of each file and decision
- **Why**: Serves as a reference for understanding the project history and rationale

### Design Decisions

#### 1. Tech Stack Agnostic Approach
The project structure and documentation support both Python and Node.js implementations.

**Rationale**:
- Learners may prefer different languages
- Core RAG concepts are language-agnostic
- Easier to compare implementations across languages

#### 2. Phased Development Approach
Structured as 6 sequential phases rather than a monolithic implementation.

**Rationale**:
- Each phase builds on the previous one
- Easy to track progress and learning
- Can stop at any phase and still have a working subset
- Matches natural learning progression from simple to complex

#### 3. Component Separation
Each major function (ingestion, embedding, storage, retrieval, LLM) has its own directory.

**Rationale**:
- **Testability**: Each component can be tested independently
- **Flexibility**: Easy to swap implementations (e.g., different vector databases)
- **Clarity**: Clear separation of concerns aids understanding
- **Scalability**: Components can be optimized or replaced individually

#### 4. Documentation-First Approach
Extensive documentation created before any implementation code.

**Rationale**:
- Clarifies project goals and architecture upfront
- Prevents common pitfalls by documenting best practices
- Serves as a learning resource throughout development
- Makes onboarding faster for collaborators or AI assistants

#### 5. Environment Configuration via .env
All configuration through environment variables.

**Rationale**:
- Security: API keys never in code
- Flexibility: Easy to switch between development/production
- Portability: Same code works across different setups
- Standard practice in modern development

### Technology Recommendations

#### For Beginners
- **Language**: Python (simpler syntax, better ML ecosystem)
- **Embeddings**: Sentence-Transformers (local, free, easy)
- **Vector DB**: ChromaDB (simple setup, persistent)
- **LLM**: Claude API (good balance of capability and ease)
- **UI**: Start with CLI, move to Streamlit

#### For Experienced Developers
- **Language**: Your preference (Python or Node.js)
- **Embeddings**: OpenAI text-embedding-3-small (higher quality)
- **Vector DB**: Pinecone or Qdrant (production-ready)
- **LLM**: Claude Sonnet or GPT-4 (best quality)
- **UI**: React/Next.js with FastAPI backend

### Next Steps for Developers

1. **Setup Environment**: Follow SETUP_GUIDE.md for your chosen stack
2. **Read ROADMAP.md**: Understand Phase 1 tasks
3. **Start Coding**: Begin with `src/ingestion/api_client.py` or `.js`
4. **Document Learning**: Add notes to this log as you progress

### Common Patterns to Follow

#### Error Handling
All API calls should have try-catch blocks and proper error messages.

#### Configuration
Use environment variables for all external services and configurable parameters.

#### Testing
Write unit tests for each component before moving to the next phase.

#### Logging
Add logging at key points (API calls, embedding generation, retrieval) for debugging.

### Future Enhancements to Track

As you build, document here:
- Implementation choices you made
- Challenges encountered and solutions
- Performance optimizations
- Deviations from the roadmap and why

---

## Phase 1 Implementation - 2025-12-30

### Overview
Successfully implemented the data ingestion pipeline with API fetching, data preprocessing, and text chunking.

### What Was Built

#### 1. Project Configuration
**File**: `pyproject.toml`
- Used **Poetry** for package management instead of pip/requirements.txt
- Dependencies: requests, python-dotenv, pytest
- Created Poetry script entry point: `rag-ingest`
- **Why Poetry**: Modern dependency management, better lock file handling, integrated tooling

#### 2. Configuration Module
**File**: `src/ingestion/config.py`
- Environment variable loading with python-dotenv
- Configuration dataclass with validation
- Default values for all settings
- Validates chunk size relationships (overlap < max_chunk_size)

#### 3. Data Models
**File**: `src/ingestion/models.py`
- **Post**: Represents API response from JSONPlaceholder
  - Fields: id, user_id, title, body
  - Factory method: `from_api_response()`
  - Conversion method: `to_document()`
- **Document**: Intermediate format for processing
  - Fields: id, content, metadata
  - Implements `__len__` for content length
- **Chunk**: Final chunked text with metadata
  - Fields: id, content, metadata
  - Implements `__len__` and `__str__`

**Design Decision**: Three-stage model (Post → Document → Chunk) separates concerns and allows flexibility in data sources.

#### 4. API Client
**File**: `src/ingestion/api_client.py`
- Fetches data from JSONPlaceholder API
- **Features**:
  - Exponential backoff retry logic (3 attempts)
  - Configurable timeout (default: 30s)
  - Comprehensive error handling
  - Support for fetching all posts or single post by ID
- **Custom Exception**: APIClientError for clear error messages
- **Why JSONPlaceholder**: Free, no authentication, reliable, 100 posts perfect for learning

#### 5. Preprocessor
**File**: `src/ingestion/preprocessor.py`
- Text cleaning (whitespace normalization)
- Sentence-aware chunking
- **Chunking Strategy**:
  - Target size: 500 characters (configurable)
  - Overlap: 50 characters
  - Preserves sentence boundaries when possible
  - Handles edge cases (documents smaller than chunk size, very long sentences)
- **Metadata Preservation**: All parent document metadata carried to chunks
- **Chunk Metadata**: parent_doc_id, chunk_index, total_chunks

#### 6. CLI Entry Point
**File**: `src/ingestion/main.py`
- Three-step pipeline: Fetch → Convert → Chunk
- Displays statistics (count, average chunk size)
- Shows sample chunks for verification
- **Fixed Issue**: Replaced Unicode checkmarks with [OK]/[ERROR] for Windows compatibility

#### 7. Comprehensive Test Suite
**Files**: `tests/test_*.py`
- **27 unit tests total**:
  - 7 tests for API client (mocking, retries, error handling)
  - 10 tests for data models (creation, conversion, validation)
  - 10 tests for preprocessor (chunking, overlap, metadata)
- **All tests passing**
- Used mocking for API tests to avoid external dependencies

### Implementation Decisions

#### Data Structure & Abstraction Layers

Chose three-tier model (Post → Document → Chunk):
- **Post**: API-specific structure
- **Document**: Normalized format (allows different API sources later)
- **Chunk**: Vector-ready format with metadata

**Complete Data Flow:**
```
[Data Source]    [Source Model]    [Document]    [Chunk]    [Embedding]    [VectorDB]
      |               |                |            |            |             |
  API Client    e.g. Post         Generic      Generic      Generic       Generic
                Story, etc.      Interface    Interface    Interface     Interface
```

**Key Abstraction: The Document Model**

The `Document(id, content, metadata)` class is the universal interface that decouples data sources from the processing pipeline:

```python
@dataclass
class Document:
    id: str                           # Unique identifier
    content: str                      # Text to embed
    metadata: Dict[str, Any]          # Source-specific info (title, author, etc.)
```

**Adding a New Data Source (Pattern)**

1. Create a source-specific **client** (fetches raw data from API)
2. Create a source-specific **model** (e.g., `Story`, `Article`) with a `to_document()` method
3. Use existing pipeline from `Document` onwards - no changes needed to:
   - `Preprocessor` (chunking)
   - `Embedder` (embedding generation)
   - `VectorStore` (storage and retrieval)

**Example: Adding a new source**
```python
@dataclass
class Story:
    id: int
    title: str
    text: str
    author: str

    def to_document(self) -> Document:
        return Document(
            id=f"story_{self.id}",
            content=f"{self.title}\n\n{self.text}",
            metadata={"source": "hackernews", "author": self.author}
        )
```

This separation allows easy addition of other data sources in future.

#### Chunking Strategy
- **Character-based** (not token-based) for Phase 1 simplicity
- **Sentence-aware** to preserve semantic meaning
- **Overlap** to prevent context loss at chunk boundaries
- **Metadata-rich** chunks for citation support in Phase 4

#### Error Handling
- Custom exceptions for clear error types
- Retry logic with exponential backoff
- Graceful degradation where possible

### Challenges Encountered

#### Challenge 1: Unicode Encoding on Windows
**Issue**: Unicode checkmark characters (✓, ✗) caused encoding errors on Windows console.
**Solution**: Replaced with ASCII characters [OK] and [ERROR].

#### Challenge 2: Sentence Splitting
**Issue**: Simple regex-based sentence splitting isn't perfect for all cases.
**Solution**: Implemented basic sentence splitting for Phase 1. Can enhance with NLTK in future phases.

#### Challenge 3: Chunk Overlap Implementation
**Issue**: Maintaining proper overlap while respecting sentence boundaries is complex.
**Solution**: Implemented sentence-level overlap that backtracks to include previous sentences up to overlap limit.

### Test Results

```
27 passed in 7.25s

Pipeline Output:
- Successfully fetched 100 posts
- Created 100 documents
- Created 100 chunks
- Avg chunk size: 201 characters
```

### Files Created
1. `pyproject.toml` - Poetry configuration
2. `src/__init__.py` - Package initialization
3. `src/ingestion/__init__.py` - Module exports
4. `src/ingestion/config.py` - Configuration
5. `src/ingestion/models.py` - Data models
6. `src/ingestion/api_client.py` - API fetching
7. `src/ingestion/preprocessor.py` - Text processing
8. `src/ingestion/main.py` - CLI entry point
9. `tests/__init__.py` - Test package
10. `tests/test_api_client.py` - API tests
11. `tests/test_models.py` - Model tests
12. `tests/test_preprocessor.py` - Preprocessor tests
13. `.env` - Environment configuration (from .env.example)

### Next Steps for Phase 2
- Choose embedding model (Sentence-Transformers recommended)
- Set up vector database (ChromaDB)
- Generate embeddings for chunks
- Store embeddings with metadata
- Implement basic similarity search

## Phase 2 Implementation - 2026-01-02

### Overview
Implemented embedding generation and vector storage using Sentence-Transformers and ChromaDB.

### What Was Built

#### 1. Embeddings Module (`src/embeddings/`)

**File**: `config.py`
- Configuration dataclass for embedding settings
- Environment variable support for all settings
- **Settings**:
  - `model_name`: Embedding model (default: all-MiniLM-L6-v2)
  - `cache_dir`: Model cache directory
  - `batch_size`: Batch size for embedding generation
  - `normalize_embeddings`: Whether to L2-normalize embeddings
  - `show_progress`: Progress bar toggle

**File**: `embedder.py`
- **Embedder class**: Main embedding generator using Sentence-Transformers
- **Features**:
  - Lazy model loading (model not loaded until first use)
  - Single text embedding (`embed_text`)
  - Batch text embedding (`embed_texts`)
  - Chunk embedding with metadata preservation (`embed_chunks`)
  - Normalized embeddings for cosine similarity
- **Why Sentence-Transformers**: Free, local, good quality, no API key needed

**File**: `main.py`
- Full pipeline CLI: fetch → preprocess → embed → store
- Includes demo query at the end
- Progress reporting at each step

#### 2. Vector Database Module (`src/vector_db/`)

**File**: `config.py`
- Configuration for ChromaDB
- **Settings**:
  - `persist_directory`: Where to store the database
  - `collection_name`: Name of the vector collection
  - `distance_metric`: Similarity metric (cosine, l2, ip)

**File**: `store.py`
- **VectorStore class**: ChromaDB wrapper
- **Features**:
  - Lazy client/collection initialization
  - Add documents with embeddings and metadata
  - Direct integration with Embedder output format
  - Query by embedding vector
  - Query by text (auto-embeds the query)
  - Collection management (count, clear, delete)
  - Persistent storage across sessions
- **Why ChromaDB**: Easy setup, persistent, good documentation, supports metadata filtering

#### 3. Test Suite Additions

**File**: `tests/test_embedder.py` (9 tests)
- Configuration tests
- Lazy loading verification
- Single and batch embedding tests
- Dimension and normalization checks
- Semantic similarity verification

**File**: `tests/test_vector_store.py` (10 tests)
- Configuration tests
- Document addition tests
- Query tests (vector and text-based)
- Persistence verification
- Collection management tests

### Implementation Decisions

#### Embedding Model Choice: all-MiniLM-L6-v2
- **Dimension**: 384 (good balance of size and quality)
- **Speed**: Fast inference, suitable for learning
- **Quality**: Good semantic similarity for general text
- **Cost**: Free, runs locally

#### Vector Database Choice: ChromaDB
- **Simplicity**: Single dependency, easy API
- **Persistence**: Built-in file-based storage
- **Metadata**: Full metadata support for filtering
- **Distance Metrics**: Supports cosine, L2, inner product

#### Architecture Decisions
- **Lazy Loading**: Models loaded on first use, not at import
- **Normalization**: Embeddings normalized for cosine similarity
- **Batch Processing**: Configurable batch size for memory management
- **Telemetry Disabled**: ChromaDB telemetry turned off

### Test Results

```
46 tests passed
Pipeline Output:
- Fetched 100 posts
- Created 100 chunks
- Generated 100 embeddings (384 dimensions)
- Stored 100 documents in ChromaDB
- Demo query returned relevant results
```

### Files Created
1. `src/embeddings/__init__.py` - Module exports
2. `src/embeddings/config.py` - Embedding configuration
3. `src/embeddings/embedder.py` - Embedder class
4. `src/embeddings/main.py` - CLI entry point
5. `src/vector_db/__init__.py` - Module exports
6. `src/vector_db/config.py` - Vector DB configuration
7. `src/vector_db/store.py` - VectorStore class
8. `tests/test_embedder.py` - Embedding tests
9. `tests/test_vector_store.py` - Vector store tests

### Usage

```bash
# Run the embedding pipeline
poetry run python -m src.embeddings.main

# Or use the poetry script
poetry run rag-embed
```

### Next Steps for Phase 3
- Implement query processing module
- Add similarity search with configurable threshold
- Implement re-ranking (optional)
- Add metadata filtering support

---

## Phase 3 Implementation - 2026-01-03

### Overview
Implemented query processing and retrieval with semantic similarity search, configurable thresholds, and an interactive CLI.

### What Was Built

#### 1. Retrieval Module (`src/retrieval/`)

**File**: `config.py`
- Configuration for retrieval operations
- **Settings**:
  - `top_k`: Number of results to retrieve (default: 5)
  - `similarity_threshold`: Minimum similarity score (default: 0.0)

**File**: `query_processor.py`
- **QueryProcessor class**: Prepares user queries for retrieval
- **Features**:
  - Query cleaning (whitespace normalization, special char removal)
  - Query embedding using the same model as documents
  - Returns ProcessedQuery with original, cleaned text, and embedding

**File**: `retriever.py`
- **Retriever class**: Main retrieval interface
- **Features**:
  - Semantic similarity search via vector store
  - Distance-to-similarity conversion (similarity = 1 - distance)
  - Configurable threshold filtering
  - Metadata filtering support
  - Lazy loading of dependencies
- **RetrievalResult**: Single result with id, content, score, metadata
- **RetrievalResponse**: Collection of results with context helpers

**File**: `main.py`
- Interactive CLI for querying
- Single query mode via command-line argument
- In-session options: `k=N` (results), `t=N` (threshold)
- Displays results with scores, metadata, and combined context

#### 2. Understanding Similarity Scores

ChromaDB returns **distance** (lower = more similar). We convert to **similarity**:
```
similarity = 1.0 - distance
```

**Similarity Score Interpretation (with real English text):**

| Score | Meaning | Example |
|-------|---------|---------|
| 1.0 | Identical | Same exact text |
| 0.95+ | Near-identical | "How do I" vs "How do you" |
| 0.8-0.95 | Same intent | Rephrased questions |
| 0.7-0.8 | Synonyms | "coding" vs "programming" |
| 0.5-0.7 | Related | Contains key terms |
| 0.3-0.5 | Topically related | Same domain |
| <0.3 | Unrelated | Different topics |

**Note**: Lorem ipsum / random text scores 0.1-0.3 regardless of query.

#### 3. Choosing a Similarity Threshold

| Use Case | Threshold | Reasoning |
|----------|-----------|-----------|
| FAQ/Support bots | 0.7-0.8 | High precision needed |
| Document search | 0.4-0.6 | Balance precision/recall |
| RAG for LLM | 0.3-0.4 | Let LLM filter irrelevant |
| Research/exploration | 0.0-0.2 | Broad results |

**Recommended for RAG**: `0.3` - Filters clearly unrelated content while keeping borderline-relevant docs for the LLM to evaluate.

**Common approaches:**
1. **No threshold + top-k**: Return top-k regardless of score (most common)
2. **Threshold + top-k**: Filter below threshold, then take top-k
3. **Dynamic threshold**: Include results within X of best match

#### 4. Improving Retrieval Accuracy

When vector search alone isn't sufficient (e.g., exact phrase matching), there are three main approaches to improve accuracy:

##### Approach 1: Smaller Chunks

**Problem:** Large chunks (500+ chars) dilute specific terms in the embedding.

**Solution:** Reduce chunk size to 200-300 characters.

```
Before (500 char chunk):
  "JSON formatters, JWT decoder, Regex tester, diff checker..."
  Query "regex tester" → similarity 0.17 (diluted)

After (200 char chunk):
  "Regex tester, diff checker, image utilities"
  Query "regex tester" → similarity 0.60+ (focused)
```

| Pros | Cons |
|------|------|
| Higher precision for specific queries | Loses surrounding context |
| Simple to implement (config change) | More chunks = more storage |
| Better for keyword-like searches | May fragment coherent paragraphs |

**When to use:** When users search for specific terms/features rather than concepts.

##### Approach 2: Hybrid Search (BM25 + Vector)

**Problem:** Vector search captures meaning but misses exact word matches.

**Solution:** Combine keyword search (BM25) with semantic search (vectors).

```
Query: "regex tester"

BM25 Search:
  - Finds documents containing exact words "regex" and "tester"
  - Uses TF-IDF scoring (term frequency × inverse document frequency)
  - Great for exact matches, misses synonyms

Vector Search:
  - Finds semantically similar documents
  - Understands "pattern matching" ≈ "regex"
  - May miss exact word matches in large chunks

Hybrid (Combined):
  - BM25 finds exact matches → high score for "regex tester" doc
  - Vector finds semantic matches → related programming docs
  - Fusion combines rankings → best of both worlds
```

**Score Fusion Methods:**

1. **Reciprocal Rank Fusion (RRF):**
   ```
   RRF_score = 1/(k + rank_bm25) + 1/(k + rank_vector)
   ```
   - Combines rankings, not raw scores
   - No normalization needed
   - k=60 is typical constant

2. **Weighted Sum:**
   ```
   score = α × vector_score + (1-α) × bm25_score
   ```
   - Requires score normalization
   - α controls balance (0.5 = equal weight)

| Pros | Cons |
|------|------|
| Best of keyword + semantic | More complex implementation |
| Handles exact matches well | Requires BM25 index storage |
| Industry standard for production | Need to tune fusion weights |

**When to use:** Production RAG systems where both exact and semantic matching matter.

##### Approach 3: Cross-Encoder Re-ranking

**Problem:** Bi-encoders (current approach) encode query and document separately, losing fine-grained interaction.

**Solution:** Use cross-encoder to re-rank top candidates.

```
Stage 1: Bi-Encoder (Fast, Rough)
  Query → Embedding → Top 100 from vector DB

Stage 2: Cross-Encoder (Slow, Precise)
  For each candidate:
    Input: "[Query] [SEP] [Document]"
    Output: Relevance score (0-1)
  Re-rank by cross-encoder score
  Return top 5
```

**Why cross-encoders are more accurate:**

| Bi-Encoder | Cross-Encoder |
|------------|---------------|
| Encodes query and doc separately | Sees query AND doc together |
| Fast: O(1) vector lookup | Slow: O(n) per query-doc pair |
| Can't see word overlap directly | Token-level attention between both |
| Good for retrieval | Good for re-ranking |

```python
# Bi-encoder (current)
query_emb = encode("regex tester")
doc_emb = encode("JSON formatters, regex tester, diff...")
similarity = dot(query_emb, doc_emb)  # 0.17 (diluted)

# Cross-encoder
score = cross_encode("regex tester [SEP] JSON formatters, regex tester, diff...")
# 0.85 - sees "regex tester" appears in both!
```

| Pros | Cons |
|------|------|
| Most accurate | Can't pre-compute, slow |
| Token-level comparison | Only practical for top-N re-ranking |
| Handles exact matches perfectly | Adds 100-500ms latency |

**When to use:** High-stakes queries where accuracy matters more than speed.

##### Comparison Summary

| Approach | Accuracy | Speed | Complexity | Best For |
|----------|----------|-------|------------|----------|
| Smaller chunks | Medium | Fast | Low | Specific term searches |
| Hybrid (BM25+Vector) | High | Medium | Medium | Production RAG |
| Cross-encoder re-rank | Highest | Slow | Medium | High-stakes queries |

### Test Results

```
22 retrieval tests passed

Similarity test with real English documents:
Query: "How do I learn programming?"
- Identical text:     1.0000
- Near-identical:     0.9671
- Same intent:        0.9201
- Synonym (coding):   0.8353
- Related content:    0.5431
- Unrelated (cat):    0.1266
```

#### Hybrid Search Results (Phase 3.1)

After implementing BM25 + Vector hybrid search:

```
33 BM25 and hybrid retriever tests passed

Query: "Regex tester, diff checker, image utilities"
Document: "Show HN: Dailydev.in - 30 Free Developer Tools"
Content includes: "Regex tester, Diff checker, Image utilities..."

Mode           | Score   | Rank | Analysis
---------------|---------|------|------------------------------------------
Vector only    | 0.3184  | #1   | Low similarity (chunk dilution)
BM25 only      | 27.0076 | #1   | High score (exact keyword matches)
Hybrid (RRF)   | 0.0328  | #1   | Best of both - ranks correctly

Result: Hybrid search successfully finds exact keyword matches that
        vector search struggles with due to semantic dilution.
```

**Files created for hybrid search:**
- `src/retrieval/bm25_index.py` - BM25 keyword search index
- `src/retrieval/hybrid_retriever.py` - Hybrid retriever with RRF
- `tests/test_bm25_index.py` - 15 BM25 tests
- `tests/test_hybrid_retriever.py` - 18 hybrid retriever tests

**Files modified:**
- `src/retrieval/main.py` - Updated to use HybridRetriever by default
- `src/ingestion/hn_main.py` - Added BM25 index building (step 6/6)

**CLI Usage:**
```bash
# Default: hybrid mode (with vector threshold filtering)
poetry run rag-query "your query"

# Override mode in interactive mode
Query> mode=vector search terms
Query> mode=bm25 search terms
Query> mode=hybrid search terms

# Set threshold (applies to vector similarity in hybrid mode)
Query> t=0.3 programming tutorials
```

**Hybrid Mode Threshold Behavior:**
- In hybrid mode, the similarity threshold applies to **vector scores only**
- Documents must meet the vector threshold even if BM25 ranked them highly
- This prevents semantically irrelevant results (low vector similarity) from appearing just because they contain keyword matches
- BM25 scores are not thresholded (they're unbounded and corpus-dependent)
- Example: With threshold=0.3, a document with vector=0.25 and BM25=50.0 will be **filtered out**

### Files Created
1. `src/retrieval/__init__.py` - Module exports
2. `src/retrieval/config.py` - Retrieval configuration
3. `src/retrieval/query_processor.py` - Query processing
4. `src/retrieval/retriever.py` - Main retriever class
5. `src/retrieval/main.py` - Interactive CLI
6. `tests/test_retrieval.py` - 22 tests

### Usage

```bash
# Interactive mode
poetry run rag-query

# Single query
poetry run rag-query "your question here"

# In interactive mode:
# - Type query and press Enter
# - Use k=3 to change result count
# - Use t=0.5 to change threshold
# - Type 'quit' to exit
```

### Current Database State
- **100 documents** from JSONPlaceholder API
- Lorem ipsum-like Latin text (low similarity scores expected)
- To test with real data, re-run embedding pipeline with different source

### Next Steps for Phase 4
- Integrate LLM (Claude API) for response generation
- Design RAG prompt template with context injection
- Add citation support in responses
- Implement streaming responses

---

## Pipeline Refactoring - 2026-01-04

### Overview
Major refactoring to improve code organization, remove deprecated code, and split the monolithic ingestion pipeline into modular stages.

### Changes Made

#### 1. Removed JSONPlaceholder Code
The original mock API (JSONPlaceholder) was removed in favor of real Hacker News data:
- **Deleted**: `src/ingestion/api_client.py` - JSONPlaceholder client
- **Deleted**: `tests/test_api_client.py` - Related tests
- **Updated**: `src/ingestion/config.py` - Removed API settings, kept chunking config

#### 2. Unified Data Models
Merged and simplified data models:
- **Before**: `Post` (JSONPlaceholder), `Story` (HN) in separate files
- **After**: Single `Article` class in `src/ingestion/models.py`
- **Deleted**: `src/ingestion/hn_models.py` (merged into models.py)
- **Added**: JSON serialization (`to_dict`, `from_dict`, `save_to_json`, `load_from_json`)

#### 3. Split Pipeline Architecture

**Before (Monolithic):**
```
rag-ingest → fetch → chunk → embed → store → BM25 (all in one)
```

**After (Modular):**
```
rag-fetch   → Fetch articles from HN → Save to data/raw/articles.json
rag-process → Load JSON → chunk → embed → store → BM25 index
rag-ingest  → Convenience wrapper (calls fetch + process)
rag-query   → Query the RAG system
```

**New Module Structure:**
```
src/
├── ingestion/     # rag-fetch: bring data in from external sources
│   ├── fetch.py   # CLI for fetching articles
│   ├── main.py    # Convenience wrapper (fetch + process)
│   ├── models.py  # Article, Document, Chunk
│   ├── hn_client.py
│   └── preprocessor.py
├── indexing/      # rag-process: build searchable index
│   ├── __init__.py
│   └── process.py # CLI for building index
├── retrieval/     # rag-query: search the index
├── embeddings/    # Library: embedding generation
└── vector_db/     # Library: vector storage
```

#### 4. Architecture Options Considered

| Option | Description | Decision |
|--------|-------------|----------|
| **A: Monolithic** | One command does everything | Original design |
| **B: Split Fetch/Process** | Separate I/O from CPU work | **Chosen** |
| **C: Granular Stages** | Separate CLI per stage | Too complex |

**Why Option B:**
- Separates I/O-bound work (API fetching) from CPU-bound work (embedding)
- Can re-process with different settings without re-fetching
- Intermediate JSON allows inspection and debugging
- Good balance of flexibility and simplicity

#### 5. CLI Commands

| Command | Entry Point | Purpose |
|---------|-------------|---------|
| `rag-fetch` | `src.ingestion.fetch:main` | Fetch articles from HN, save to JSON |
| `rag-process` | `src.indexing.process:main` | Build index from JSON |
| `rag-ingest` | `src.ingestion.main:main` | Convenience: fetch + process |
| `rag-query` | `src.retrieval.main:main` | Query the RAG system |

**Usage:**
```bash
# Two-stage workflow (recommended for development)
poetry run rag-fetch --limit 100
poetry run rag-process

# One-command workflow
poetry run rag-ingest 100

# Query
poetry run rag-query "your question"
```

#### 6. Data Directory Structure

```
data/
├── raw/              # Fetched articles (articles.json)
├── chroma_db/        # Vector database
└── bm25_index.pkl    # BM25 index
```

### Files Changed Summary

| File | Action |
|------|--------|
| `src/ingestion/api_client.py` | **Deleted** |
| `src/ingestion/hn_models.py` | **Deleted** (merged) |
| `tests/test_api_client.py` | **Deleted** |
| `tests/test_hn_models.py` | **Deleted** (merged) |
| `src/ingestion/fetch.py` | **Created** |
| `src/indexing/__init__.py` | **Created** |
| `src/indexing/process.py` | **Created** |
| `src/ingestion/models.py` | Merged Article, added serialization |
| `src/ingestion/config.py` | Removed API settings |
| `src/ingestion/main.py` | Refactored as wrapper |
| `src/ingestion/hn_client.py` | Updated to use Article |
| `tests/test_models.py` | Merged Article tests |
| `tests/test_hn_client.py` | Updated imports |
| `pyproject.toml` | Added new CLI scripts |

### Test Results
```
117 tests passed
```

---

## Phase 4 Implementation (To be added)

## Phase 5 Implementation (To be added)

## Phase 6 Implementation (To be added)

---

**Last Updated**: 2026-01-04
**Status**: Phase 3 completed with hybrid search. Pipeline refactored into modular stages (fetch → process → query).
