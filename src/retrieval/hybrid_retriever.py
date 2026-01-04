"""Hybrid retriever combining BM25 keyword search and vector semantic search."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from src.retrieval.bm25_index import BM25Index
from src.retrieval.config import RetrievalConfig
from src.retrieval.query_processor import QueryProcessor
from src.retrieval.retriever import RetrievalResult, RetrievalResponse
from src.vector_db import VectorStore, VectorDBConfig


@dataclass
class HybridConfig:
    """Configuration for hybrid retrieval."""

    # Search mode: "vector", "bm25", or "hybrid"
    search_mode: str = "hybrid"

    # Path to BM25 index file
    bm25_index_path: str = "./data/bm25_index.pkl"

    # RRF constant (prevents high scores for top ranks)
    rrf_k: int = 60


def reciprocal_rank_fusion(
    result_lists: List[List[Tuple[str, float]]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """Combine multiple result lists using Reciprocal Rank Fusion.

    RRF score = sum(1 / (k + rank)) across all result lists.

    This method is preferred over weighted sum because:
    - Doesn't require score normalization
    - Works well when scores are on different scales
    - Proven effective in information retrieval

    Args:
        result_lists: List of [(doc_id, score), ...] lists.
        k: Constant to prevent very high scores for top ranks (default 60).

    Returns:
        List of (doc_id, rrf_score) sorted by score descending.
    """
    scores: Dict[str, float] = {}

    for results in result_lists:
        for rank, (doc_id, _) in enumerate(results):
            # RRF formula: 1 / (k + rank), where rank is 0-indexed
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

    # Sort by score descending
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


class HybridRetriever:
    """Retriever that combines BM25 keyword search with vector semantic search.

    Supports three modes:
    - "vector": Pure semantic search using embeddings
    - "bm25": Pure keyword search using BM25
    - "hybrid": Combined search using Reciprocal Rank Fusion

    Example:
        retriever = HybridRetriever(config=HybridConfig(search_mode="hybrid"))
        results = retriever.retrieve("regex tester tool")
    """

    def __init__(
        self,
        config: Optional[HybridConfig] = None,
        retrieval_config: Optional[RetrievalConfig] = None,
        vector_store: Optional[VectorStore] = None,
        bm25_index: Optional[BM25Index] = None,
        query_processor: Optional[QueryProcessor] = None,
    ):
        """Initialize the hybrid retriever.

        Args:
            config: Hybrid retrieval configuration.
            retrieval_config: Base retrieval configuration.
            vector_store: Vector store instance.
            bm25_index: BM25 index instance.
            query_processor: Query processor for embedding queries.
        """
        self.config = config or HybridConfig()
        self.retrieval_config = retrieval_config or RetrievalConfig.from_env()
        self._vector_store = vector_store
        self._bm25_index = bm25_index
        self._query_processor = query_processor

    @property
    def vector_store(self) -> VectorStore:
        """Lazy-load the vector store."""
        if self._vector_store is None:
            db_config = VectorDBConfig.from_env()
            self._vector_store = VectorStore(db_config)
        return self._vector_store

    @property
    def bm25_index(self) -> BM25Index:
        """Lazy-load the BM25 index."""
        if self._bm25_index is None:
            self._bm25_index = BM25Index()
            self._bm25_index.load(self.config.bm25_index_path)
        return self._bm25_index

    @property
    def query_processor(self) -> QueryProcessor:
        """Lazy-load the query processor."""
        if self._query_processor is None:
            self._query_processor = QueryProcessor()
        return self._query_processor

    def _distance_to_similarity(self, distance: float) -> float:
        """Convert distance to similarity score."""
        return 1.0 - distance

    def _get_vector_results(
        self, query: str, top_k: int
    ) -> List[Tuple[str, float]]:
        """Get results from vector search.

        Returns:
            List of (doc_id, similarity_score) tuples.
        """
        processed = self.query_processor.process(query)

        raw_results = self.vector_store.query(
            query_embedding=processed.embedding,
            n_results=top_k,
        )

        results = []
        for i in range(len(raw_results["ids"][0])):
            doc_id = raw_results["ids"][0][i]
            distance = raw_results["distances"][0][i]
            similarity = self._distance_to_similarity(distance)
            results.append((doc_id, similarity))

        return results

    def _get_bm25_results(
        self, query: str, top_k: int
    ) -> List[Tuple[str, float]]:
        """Get results from BM25 search.

        Returns:
            List of (doc_id, bm25_score) tuples.
        """
        return self.bm25_index.search(query, top_k=top_k)

    def _get_document_content(self, doc_id: str) -> Tuple[str, Dict[str, Any]]:
        """Fetch document content and metadata from vector store.

        Args:
            doc_id: Document ID to fetch.

        Returns:
            Tuple of (content, metadata).
        """
        # Query with a dummy embedding to get the document by ID
        results = self.vector_store.collection.get(
            ids=[doc_id],
            include=["documents", "metadatas"],
        )

        if results["documents"] and results["documents"][0]:
            content = results["documents"][0]
            metadata = results["metadatas"][0] if results["metadatas"] else {}
            return content, metadata

        return "", {}

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        mode: Optional[str] = None,
    ) -> RetrievalResponse:
        """Retrieve relevant documents using configured search mode.

        Args:
            query: User query string.
            top_k: Number of results (overrides config).
            threshold: Similarity threshold (overrides config).
            mode: Search mode override ("vector", "bm25", "hybrid").

        Returns:
            RetrievalResponse with results.
        """
        k = top_k or self.retrieval_config.top_k
        thresh = threshold if threshold is not None else self.retrieval_config.similarity_threshold
        search_mode = mode or self.config.search_mode

        # Get candidate results (fetch more for fusion)
        fetch_k = k * 3 if search_mode == "hybrid" else k

        # Track original vector scores for hybrid threshold checking
        vector_scores_map = {}

        if search_mode == "vector":
            scored_results = self._get_vector_results(query, fetch_k)
        elif search_mode == "bm25":
            scored_results = self._get_bm25_results(query, fetch_k)
        else:  # hybrid
            vector_results = self._get_vector_results(query, fetch_k)
            bm25_results = self._get_bm25_results(query, fetch_k)

            # Store original vector scores for threshold checking
            vector_scores_map = {doc_id: score for doc_id, score in vector_results}

            # Combine using RRF
            scored_results = reciprocal_rank_fusion(
                [vector_results, bm25_results],
                k=self.config.rrf_k,
            )

        # Take top-k and build results
        results = []
        for doc_id, score in scored_results[:k]:
            # Apply vector similarity threshold
            if search_mode == "vector" and score < thresh:
                continue

            # In hybrid mode, check original vector similarity
            if search_mode == "hybrid":
                vector_similarity = vector_scores_map.get(doc_id, 0.0)
                if vector_similarity < thresh:
                    # Skip documents that don't meet vector threshold
                    # even if BM25 ranked them highly
                    continue

            content, metadata = self._get_document_content(doc_id)
            if not content:
                continue

            result = RetrievalResult(
                id=doc_id,
                content=content,
                score=score,
                metadata=metadata,
            )
            results.append(result)

        return RetrievalResponse(
            query=query,
            results=results,
            total_found=len(results),
        )

    def compare_modes(
        self, query: str, top_k: int = 5
    ) -> Dict[str, RetrievalResponse]:
        """Compare results from all search modes.

        Useful for debugging and understanding how different
        modes rank documents.

        Args:
            query: Query to test.
            top_k: Number of results per mode.

        Returns:
            Dict mapping mode name to RetrievalResponse.
        """
        return {
            "vector": self.retrieve(query, top_k=top_k, mode="vector"),
            "bm25": self.retrieve(query, top_k=top_k, mode="bm25"),
            "hybrid": self.retrieve(query, top_k=top_k, mode="hybrid"),
        }
