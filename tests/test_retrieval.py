"""Tests for the retrieval module."""

import pytest
import tempfile
import shutil

from src.retrieval.config import RetrievalConfig
from src.retrieval.query_processor import QueryProcessor, ProcessedQuery
from src.retrieval.retriever import Retriever, RetrievalResult, RetrievalResponse
from src.vector_db import VectorStore, VectorDBConfig
from src.embeddings import Embedder, EmbeddingConfig


class TestRetrievalConfig:
    """Tests for RetrievalConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetrievalConfig()
        assert config.top_k == 5
        assert config.similarity_threshold == 0.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = RetrievalConfig(
            top_k=10,
            similarity_threshold=0.5,
        )
        assert config.top_k == 10
        assert config.similarity_threshold == 0.5


class TestQueryProcessor:
    """Tests for QueryProcessor."""

    @pytest.fixture
    def processor(self):
        """Create a query processor for testing."""
        config = EmbeddingConfig(show_progress=False)
        embedder = Embedder(config)
        return QueryProcessor(embedder)

    def test_clean_query_strips_whitespace(self, processor):
        """Test that whitespace is stripped."""
        assert processor.clean_query("  hello world  ") == "hello world"

    def test_clean_query_normalizes_spaces(self, processor):
        """Test that multiple spaces are normalized."""
        assert processor.clean_query("hello    world") == "hello world"

    def test_clean_query_preserves_punctuation(self, processor):
        """Test that common punctuation is preserved."""
        assert processor.clean_query("Hello, world!") == "Hello, world!"
        assert processor.clean_query("What's this?") == "What's this?"

    def test_process_returns_processed_query(self, processor):
        """Test that process returns a ProcessedQuery."""
        result = processor.process("test query")

        assert isinstance(result, ProcessedQuery)
        assert result.original == "test query"
        assert result.cleaned == "test query"
        assert isinstance(result.embedding, list)
        assert len(result.embedding) == 384  # all-MiniLM-L6-v2 dimension

    def test_process_cleans_query(self, processor):
        """Test that process cleans the query."""
        result = processor.process("  messy   query  ")

        assert result.original == "  messy   query  "
        assert result.cleaned == "messy query"


class TestRetrievalResult:
    """Tests for RetrievalResult."""

    def test_result_creation(self):
        """Test creating a retrieval result."""
        result = RetrievalResult(
            id="doc_1",
            content="Test content",
            score=0.85,
            metadata={"source": "test"},
        )

        assert result.id == "doc_1"
        assert result.content == "Test content"
        assert result.score == 0.85
        assert result.metadata == {"source": "test"}

    def test_result_str_short_content(self):
        """Test string representation with short content."""
        result = RetrievalResult(id="1", content="Short", score=0.9)
        assert "[0.9000] Short" in str(result)

    def test_result_str_long_content(self):
        """Test string representation with long content."""
        long_content = "x" * 200
        result = RetrievalResult(id="1", content=long_content, score=0.9)
        assert "..." in str(result)
        assert len(str(result)) < len(long_content)


class TestRetrievalResponse:
    """Tests for RetrievalResponse."""

    def test_has_results_true(self):
        """Test has_results when results exist."""
        response = RetrievalResponse(
            query="test",
            results=[RetrievalResult(id="1", content="c", score=0.9)],
            total_found=1,
        )
        assert response.has_results is True

    def test_has_results_false(self):
        """Test has_results when no results."""
        response = RetrievalResponse(query="test", results=[], total_found=0)
        assert response.has_results is False

    def test_get_context(self):
        """Test combining results into context."""
        response = RetrievalResponse(
            query="test",
            results=[
                RetrievalResult(id="1", content="First", score=0.9),
                RetrievalResult(id="2", content="Second", score=0.8),
            ],
            total_found=2,
        )

        context = response.get_context(separator=" | ")
        assert context == "First | Second"

    def test_get_context_with_sources(self):
        """Test context with source citations."""
        response = RetrievalResponse(
            query="test",
            results=[
                RetrievalResult(id="1", content="Content 1", score=0.9, metadata={"title": "Doc A"}),
                RetrievalResult(id="2", content="Content 2", score=0.8, metadata={}),
            ],
            total_found=2,
        )

        context = response.get_context_with_sources()
        assert "[Source 1: Doc A]" in context
        assert "[Source 2]" in context
        assert "Content 1" in context
        assert "Content 2" in context


class TestRetriever:
    """Tests for the Retriever class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for the test database."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def embedder(self):
        """Create an embedder for testing."""
        config = EmbeddingConfig(show_progress=False)
        return Embedder(config)

    @pytest.fixture
    def populated_store(self, temp_dir, embedder):
        """Create a vector store with test data."""
        config = VectorDBConfig(
            persist_directory=temp_dir,
            collection_name="test_retrieval",
        )
        store = VectorStore(config)

        # Add test documents
        texts = [
            "Python is a popular programming language for data science",
            "JavaScript is used for web development",
            "Machine learning models require training data",
            "Cats are fluffy domestic animals",
            "Dogs are loyal pets",
        ]
        embeddings = embedder.embed_texts(texts).tolist()
        ids = [f"doc_{i}" for i in range(len(texts))]
        metadatas = [{"title": f"Document {i}", "source": "test"} for i in range(len(texts))]

        store.add_documents(ids, embeddings, texts, metadatas)
        return store

    @pytest.fixture
    def retriever(self, populated_store, embedder):
        """Create a retriever with populated store."""
        processor = QueryProcessor(embedder)
        config = RetrievalConfig(top_k=3)
        # Suppress deprecation warning in fixture
        with pytest.warns(DeprecationWarning):
            return Retriever(
                config=config,
                vector_store=populated_store,
                query_processor=processor,
            )

    def test_retriever_emits_deprecation_warning(self):
        """Test that Retriever emits deprecation warning."""
        with pytest.warns(DeprecationWarning, match="Use HybridRetriever"):
            Retriever(config=RetrievalConfig())

    def test_retrieve_returns_response(self, retriever):
        """Test that retrieve returns a RetrievalResponse."""
        response = retriever.retrieve("programming")

        assert isinstance(response, RetrievalResponse)
        assert response.query == "programming"

    def test_retrieve_finds_relevant_docs(self, retriever):
        """Test that relevant documents are retrieved."""
        response = retriever.retrieve("programming languages")

        assert response.has_results
        # Programming-related docs should be retrieved
        contents = [r.content for r in response.results]
        assert any("Python" in c or "JavaScript" in c for c in contents)

    def test_retrieve_respects_top_k(self, retriever):
        """Test that top_k limits results."""
        response = retriever.retrieve("animals", top_k=2)
        assert len(response.results) <= 2

    def test_retrieve_with_threshold(self, retriever):
        """Test similarity threshold filtering."""
        # Very high threshold should filter most results
        response = retriever.retrieve("random xyz query", threshold=0.99)
        assert len(response.results) == 0

    def test_retrieve_includes_scores(self, retriever):
        """Test that scores are included in results."""
        response = retriever.retrieve("data science")

        assert response.has_results
        for result in response.results:
            assert result.score > 0
            assert result.score <= 1

    def test_retrieve_includes_metadata(self, retriever):
        """Test that metadata is included in results."""
        response = retriever.retrieve("programming")

        assert response.has_results
        for result in response.results:
            assert "title" in result.metadata
            assert "source" in result.metadata

    def test_distance_to_similarity_conversion(self, retriever):
        """Test distance to similarity conversion."""
        # For cosine, distance 0 = similarity 1
        assert retriever._distance_to_similarity(0.0) == 1.0
        # distance 0.5 = similarity 0.5
        assert retriever._distance_to_similarity(0.5) == 0.5
        # distance 1 = similarity 0
        assert retriever._distance_to_similarity(1.0) == 0.0
