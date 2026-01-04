"""Main retriever class for semantic search."""

import warnings
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from src.retrieval.config import RetrievalConfig
from src.retrieval.query_processor import QueryProcessor, ProcessedQuery
from src.vector_db import VectorStore, VectorDBConfig
from src.embeddings import Embedder


@dataclass
class RetrievalResult:
    """A single retrieval result."""

    id: str
    content: str
    score: float  # Similarity score (1 - distance for cosine)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation of the result."""
        preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"[{self.score:.4f}] {preview}"


@dataclass
class RetrievalResponse:
    """Response containing retrieval results and query info."""

    query: str
    results: List[RetrievalResult]
    total_found: int

    @property
    def has_results(self) -> bool:
        """Check if any results were found."""
        return len(self.results) > 0

    def get_context(self, separator: str = "\n\n---\n\n") -> str:
        """Get combined context from all results.

        Args:
            separator: String to separate results.

        Returns:
            Combined content from all results.
        """
        return separator.join(r.content for r in self.results)

    def get_context_with_sources(self, separator: str = "\n\n") -> str:
        """Get context with source citations.

        Args:
            separator: String to separate results.

        Returns:
            Content with [Source N] citations.
        """
        parts = []
        for i, result in enumerate(self.results, 1):
            source_info = f"[Source {i}]"
            if result.metadata.get("title"):
                source_info = f"[Source {i}: {result.metadata['title']}]"
            parts.append(f"{source_info}\n{result.content}")
        return separator.join(parts)


class Retriever:
    """Retrieves relevant documents for queries.

    .. deprecated::
        Use HybridRetriever with mode="vector" instead.
        This class is kept for backward compatibility.
    """

    def __init__(
        self,
        config: Optional[RetrievalConfig] = None,
        vector_store: Optional[VectorStore] = None,
        query_processor: Optional[QueryProcessor] = None,
    ):
        """Initialize the retriever.

        Args:
            config: Retrieval configuration.
            vector_store: Vector store instance.
            query_processor: Query processor instance.
        """
        warnings.warn(
            "Retriever is deprecated. Use HybridRetriever with mode='vector' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.config = config or RetrievalConfig.from_env()
        self._vector_store = vector_store
        self._query_processor = query_processor

    @property
    def vector_store(self) -> VectorStore:
        """Lazy-load the vector store."""
        if self._vector_store is None:
            db_config = VectorDBConfig.from_env()
            self._vector_store = VectorStore(db_config)
        return self._vector_store

    @property
    def query_processor(self) -> QueryProcessor:
        """Lazy-load the query processor."""
        if self._query_processor is None:
            self._query_processor = QueryProcessor()
        return self._query_processor

    def _distance_to_similarity(self, distance: float) -> float:
        """Convert distance to similarity score.

        For cosine distance: similarity = 1 - distance
        ChromaDB returns distance, we want similarity (higher = better).
        """
        return 1.0 - distance

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResponse:
        """Retrieve relevant documents for a query.

        Args:
            query: User query string.
            top_k: Number of results (overrides config).
            threshold: Similarity threshold (overrides config).
            where: Metadata filter for ChromaDB.

        Returns:
            RetrievalResponse with results.
        """
        k = top_k or self.config.top_k
        thresh = threshold if threshold is not None else self.config.similarity_threshold

        # Process the query
        processed = self.query_processor.process(query)

        # Query the vector store
        raw_results = self.vector_store.query(
            query_embedding=processed.embedding,
            n_results=k,
            where=where,
        )

        # Convert to RetrievalResult objects
        results = []
        for i in range(len(raw_results["ids"][0])):
            distance = raw_results["distances"][0][i]
            similarity = self._distance_to_similarity(distance)

            # Apply threshold filter
            if similarity < thresh:
                continue

            result = RetrievalResult(
                id=raw_results["ids"][0][i],
                content=raw_results["documents"][0][i],
                score=similarity,
                metadata=raw_results["metadatas"][0][i] if raw_results["metadatas"] else {},
            )
            results.append(result)

        return RetrievalResponse(
            query=query,
            results=results,
            total_found=len(results),
        )
