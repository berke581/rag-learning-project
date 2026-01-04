"""Tests for the embeddings module."""

import pytest
import numpy as np

from src.embeddings.config import EmbeddingConfig
from src.embeddings.embedder import Embedder
from src.ingestion.models import Chunk


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EmbeddingConfig()
        assert config.model_name == "all-MiniLM-L6-v2"
        assert config.batch_size == 32
        assert config.normalize_embeddings is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = EmbeddingConfig(
            model_name="custom-model",
            batch_size=16,
            normalize_embeddings=False,
        )
        assert config.model_name == "custom-model"
        assert config.batch_size == 16
        assert config.normalize_embeddings is False


class TestEmbedder:
    """Tests for the Embedder class."""

    @pytest.fixture
    def embedder(self):
        """Create an embedder for testing."""
        config = EmbeddingConfig(show_progress=False)
        return Embedder(config)

    def test_lazy_model_loading(self):
        """Test that model is not loaded until needed."""
        config = EmbeddingConfig()
        embedder = Embedder(config)
        assert embedder._model is None

    def test_embed_text_returns_numpy_array(self, embedder):
        """Test single text embedding returns numpy array."""
        embedding = embedder.embed_text("Hello world")
        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1

    def test_embed_text_dimension(self, embedder):
        """Test embedding dimension matches model."""
        embedding = embedder.embed_text("Test text")
        assert len(embedding) == embedder.dimension

    def test_embed_texts_batch(self, embedder):
        """Test batch embedding of multiple texts."""
        texts = ["First text", "Second text", "Third text"]
        embeddings = embedder.embed_texts(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3
        assert embeddings.shape[1] == embedder.dimension

    def test_embed_chunks(self, embedder):
        """Test embedding of Chunk objects."""
        chunks = [
            Chunk(id="chunk_1", content="First chunk content", metadata={"source": "test"}),
            Chunk(id="chunk_2", content="Second chunk content", metadata={"source": "test"}),
        ]

        results = embedder.embed_chunks(chunks)

        assert len(results) == 2
        assert results[0]["id"] == "chunk_1"
        assert results[1]["id"] == "chunk_2"
        assert "embedding" in results[0]
        assert "content" in results[0]
        assert "metadata" in results[0]
        assert len(results[0]["embedding"]) == embedder.dimension

    def test_normalized_embeddings(self, embedder):
        """Test that embeddings are normalized when configured."""
        embedding = embedder.embed_text("Test normalization")
        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0, atol=1e-5)

    def test_similar_texts_have_similar_embeddings(self, embedder):
        """Test that semantically similar texts have similar embeddings."""
        text1 = "The cat sat on the mat"
        text2 = "A cat was sitting on a mat"
        text3 = "Python programming language"

        emb1 = embedder.embed_text(text1)
        emb2 = embedder.embed_text(text2)
        emb3 = embedder.embed_text(text3)

        # Cosine similarity (embeddings are normalized)
        sim_12 = np.dot(emb1, emb2)
        sim_13 = np.dot(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_12 > sim_13
