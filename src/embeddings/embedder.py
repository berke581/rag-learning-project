"""Embedding generation using Sentence-Transformers."""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from src.embeddings.config import EmbeddingConfig
from src.ingestion.models import Chunk


class Embedder:
    """Generates embeddings for text using Sentence-Transformers."""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize the embedder with configuration.

        Args:
            config: Embedding configuration. Uses defaults if not provided.
        """
        self.config = config or EmbeddingConfig.from_env()
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            self._model = SentenceTransformer(
                self.config.model_name,
                cache_folder=self.config.cache_dir,
            )
        return self._model

    @property
    def dimension(self) -> int:
        """Return the embedding dimension for the loaded model."""
        return self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            numpy array of shape (dimension,)
        """
        embedding = self.model.encode(
            text,
            normalize_embeddings=self.config.normalize_embeddings,
            show_progress_bar=False,
        )
        return np.array(embedding)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            numpy array of shape (num_texts, dimension)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            normalize_embeddings=self.config.normalize_embeddings,
            show_progress_bar=self.config.show_progress,
        )
        return np.array(embeddings)

    def embed_chunks(self, chunks: List[Chunk]) -> List[dict]:
        """Generate embeddings for chunks with metadata.

        Args:
            chunks: List of Chunk objects to embed.

        Returns:
            List of dicts with 'id', 'embedding', and 'metadata' keys.
        """
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_texts(texts)

        results = []
        for chunk, embedding in zip(chunks, embeddings):
            results.append({
                "id": chunk.id,
                "embedding": embedding.tolist(),
                "content": chunk.content,
                "metadata": chunk.metadata,
            })
        return results
