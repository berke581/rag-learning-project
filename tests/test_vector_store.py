"""Tests for the vector database module."""

import pytest
import tempfile
import shutil
import os

from src.vector_db.config import VectorDBConfig
from src.vector_db.store import VectorStore
from src.embeddings.embedder import Embedder
from src.embeddings.config import EmbeddingConfig


class TestVectorDBConfig:
    """Tests for VectorDBConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = VectorDBConfig()
        assert config.collection_name == "rag_documents"
        assert config.distance_metric == "cosine"

    def test_custom_config(self):
        """Test custom configuration."""
        config = VectorDBConfig(
            persist_directory="/custom/path",
            collection_name="custom_collection",
            distance_metric="l2",
        )
        assert config.persist_directory == "/custom/path"
        assert config.collection_name == "custom_collection"
        assert config.distance_metric == "l2"


class TestVectorStore:
    """Tests for the VectorStore class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for the test database."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a vector store for testing."""
        config = VectorDBConfig(
            persist_directory=temp_dir,
            collection_name="test_collection",
        )
        return VectorStore(config)

    @pytest.fixture
    def embedder(self):
        """Create an embedder for testing."""
        config = EmbeddingConfig(show_progress=False)
        return Embedder(config)

    def test_add_documents(self, store):
        """Test adding documents to the store."""
        ids = ["doc_1", "doc_2"]
        embeddings = [[0.1] * 384, [0.2] * 384]  # Fake embeddings
        documents = ["First document", "Second document"]
        metadatas = [{"source": "test"}, {"source": "test"}]

        store.add_documents(ids, embeddings, documents, metadatas)
        assert store.count() == 2

    def test_add_embedded_chunks(self, store):
        """Test adding embedded chunks from Embedder output format."""
        embedded_chunks = [
            {
                "id": "chunk_1",
                "embedding": [0.1] * 384,
                "content": "First chunk",
                "metadata": {"source": "test"},
            },
            {
                "id": "chunk_2",
                "embedding": [0.2] * 384,
                "content": "Second chunk",
                "metadata": {"source": "test"},
            },
        ]

        store.add_embedded_chunks(embedded_chunks)
        assert store.count() == 2

    def test_query(self, store):
        """Test querying the store."""
        # Add test documents
        ids = ["doc_1", "doc_2", "doc_3"]
        embeddings = [
            [1.0] + [0.0] * 383,  # Points in direction 1
            [0.0, 1.0] + [0.0] * 382,  # Points in direction 2
            [0.9, 0.1] + [0.0] * 382,  # Similar to doc_1
        ]
        documents = ["Doc one", "Doc two", "Doc three"]

        store.add_documents(ids, embeddings, documents)

        # Query with vector similar to doc_1
        query_embedding = [0.95, 0.05] + [0.0] * 382
        results = store.query(query_embedding, n_results=2)

        # doc_1 and doc_3 should be most similar
        assert "doc_1" in results["ids"][0] or "doc_3" in results["ids"][0]

    def test_query_text(self, store, embedder):
        """Test text-based query with real embeddings."""
        # Generate real embeddings
        texts = [
            "Python is a programming language",
            "Cats are furry animals",
            "JavaScript runs in browsers",
        ]
        embeddings = embedder.embed_texts(texts).tolist()

        ids = ["doc_1", "doc_2", "doc_3"]
        store.add_documents(ids, embeddings, texts)

        # Query for programming-related content
        results = store.query_text("coding and software", embedder, n_results=3)

        # Should return results with expected structure
        assert len(results) == 3
        result_ids = [r["id"] for r in results]
        assert "doc_1" in result_ids  # Python doc should be found
        assert "doc_3" in result_ids  # JavaScript doc should be found

    def test_query_text_returns_formatted_results(self, store, embedder):
        """Test that query_text returns properly formatted results."""
        texts = ["Test document content"]
        embeddings = embedder.embed_texts(texts).tolist()

        store.add_documents(
            ids=["test_id"],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"key": "value"}],
        )

        results = store.query_text("test", embedder, n_results=1)

        assert len(results) == 1
        assert "id" in results[0]
        assert "content" in results[0]
        assert "metadata" in results[0]
        assert "distance" in results[0]

    def test_count(self, store):
        """Test counting documents in the store."""
        assert store.count() == 0

        store.add_documents(["doc_1"], [[0.1] * 384], ["Doc one"])
        assert store.count() == 1

        store.add_documents(["doc_2"], [[0.2] * 384], ["Doc two"])
        assert store.count() == 2

    def test_clear(self, store):
        """Test clearing all documents."""
        store.add_documents(["doc_1", "doc_2"], [[0.1] * 384, [0.2] * 384], ["One", "Two"])
        assert store.count() == 2

        store.clear()
        assert store.count() == 0

    def test_persistence(self, temp_dir):
        """Test that data persists across store instances."""
        config = VectorDBConfig(
            persist_directory=temp_dir,
            collection_name="persist_test",
        )

        # Create store and add data
        store1 = VectorStore(config)
        store1.add_documents(["doc_1"], [[0.1] * 384], ["Persistent doc"])
        assert store1.count() == 1

        # Create new store instance pointing to same directory
        store2 = VectorStore(config)
        assert store2.count() == 1
