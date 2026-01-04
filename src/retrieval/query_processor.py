"""Query processing for the retrieval pipeline."""

import re
from typing import Optional
from dataclasses import dataclass

from src.embeddings import Embedder, EmbeddingConfig


@dataclass
class ProcessedQuery:
    """Represents a processed query ready for retrieval."""

    original: str
    cleaned: str
    embedding: list[float]


class QueryProcessor:
    """Processes user queries for retrieval."""

    def __init__(self, embedder: Optional[Embedder] = None):
        """Initialize the query processor.

        Args:
            embedder: Embedder instance. Creates one if not provided.
        """
        self._embedder = embedder

    @property
    def embedder(self) -> Embedder:
        """Lazy-load the embedder."""
        if self._embedder is None:
            config = EmbeddingConfig.from_env()
            config.show_progress = False
            self._embedder = Embedder(config)
        return self._embedder

    def clean_query(self, query: str) -> str:
        """Clean and normalize a query string.

        Args:
            query: Raw user query.

        Returns:
            Cleaned query string.
        """
        # Strip whitespace
        cleaned = query.strip()

        # Normalize whitespace (multiple spaces to single)
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Remove special characters that might cause issues
        # Keep alphanumeric, spaces, and common punctuation
        cleaned = re.sub(r'[^\w\s\-\'".,?!]', '', cleaned)

        return cleaned

    def process(self, query: str) -> ProcessedQuery:
        """Process a query for retrieval.

        Args:
            query: Raw user query.

        Returns:
            ProcessedQuery with original, cleaned text, and embedding.
        """
        cleaned = self.clean_query(query)
        embedding = self.embedder.embed_text(cleaned).tolist()

        return ProcessedQuery(
            original=query,
            cleaned=cleaned,
            embedding=embedding,
        )
