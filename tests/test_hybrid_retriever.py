"""Tests for hybrid retriever combining BM25 and vector search."""

import pytest
from unittest.mock import MagicMock, patch

from src.retrieval.hybrid_retriever import (
    HybridRetriever,
    HybridConfig,
    reciprocal_rank_fusion,
)
from src.retrieval.retriever import RetrievalResult


class TestReciprocalRankFusion:
    """Tests for RRF score fusion."""

    def test_single_list(self):
        """Test RRF with single result list."""
        results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]

        fused = reciprocal_rank_fusion([results], k=60)

        # Should maintain order
        assert fused[0][0] == "doc1"
        assert fused[1][0] == "doc2"
        assert fused[2][0] == "doc3"

    def test_two_lists_same_ranking(self):
        """Test RRF with two lists that agree on ranking."""
        list1 = [("doc1", 0.9), ("doc2", 0.8)]
        list2 = [("doc1", 0.95), ("doc2", 0.85)]

        fused = reciprocal_rank_fusion([list1, list2], k=60)

        # doc1 should still be first since both lists rank it first
        assert fused[0][0] == "doc1"
        assert fused[1][0] == "doc2"

        # doc1 should have higher score (appears in rank 0 in both)
        assert fused[0][1] > fused[1][1]

    def test_two_lists_different_ranking(self):
        """Test RRF with two lists that disagree on ranking."""
        list1 = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        list2 = [("doc3", 0.95), ("doc2", 0.85), ("doc1", 0.75)]

        fused = reciprocal_rank_fusion([list1, list2], k=60)

        # doc2 appears at rank 1 in both lists, so should score well
        # The exact winner depends on RRF calculation
        doc_ids = [doc[0] for doc in fused]
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids
        assert "doc3" in doc_ids

    def test_non_overlapping_lists(self):
        """Test RRF with non-overlapping result lists."""
        list1 = [("doc1", 0.9), ("doc2", 0.8)]
        list2 = [("doc3", 0.95), ("doc4", 0.85)]

        fused = reciprocal_rank_fusion([list1, list2], k=60)

        # All docs should appear
        doc_ids = [doc[0] for doc in fused]
        assert len(doc_ids) == 4
        assert set(doc_ids) == {"doc1", "doc2", "doc3", "doc4"}

    def test_partial_overlap(self):
        """Test RRF with partially overlapping lists."""
        list1 = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        list2 = [("doc2", 0.95), ("doc4", 0.85), ("doc1", 0.75)]

        fused = reciprocal_rank_fusion([list1, list2], k=60)

        # doc2 appears in both, should get boosted
        doc_ids = [doc[0] for doc in fused]
        assert len(set(doc_ids)) == 4  # 4 unique docs

    def test_empty_lists(self):
        """Test RRF with empty result lists."""
        fused = reciprocal_rank_fusion([[], []], k=60)
        assert fused == []

    def test_k_parameter_effect(self):
        """Test that k parameter affects scores but not ranking."""
        results = [("doc1", 0.9), ("doc2", 0.8)]

        fused_low_k = reciprocal_rank_fusion([results], k=10)
        fused_high_k = reciprocal_rank_fusion([results], k=100)

        # Rankings should be the same
        assert fused_low_k[0][0] == fused_high_k[0][0]

        # Scores should differ (lower k = higher scores for top ranks)
        assert fused_low_k[0][1] > fused_high_k[0][1]


class TestHybridConfig:
    """Tests for HybridConfig."""

    def test_defaults(self):
        """Test default configuration values."""
        config = HybridConfig()

        assert config.search_mode == "hybrid"
        assert config.bm25_index_path == "./data/bm25_index.pkl"
        assert config.rrf_k == 60

    def test_custom_values(self):
        """Test custom configuration values."""
        config = HybridConfig(
            search_mode="vector",
            bm25_index_path="/custom/path.pkl",
            rrf_k=100,
        )

        assert config.search_mode == "vector"
        assert config.bm25_index_path == "/custom/path.pkl"
        assert config.rrf_k == 100


class TestHybridRetriever:
    """Tests for the HybridRetriever class."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = MagicMock()
        store.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["content 1", "content 2"]],
            "metadatas": [[{"title": "Title 1"}, {"title": "Title 2"}]],
            "distances": [[0.3, 0.5]],
        }
        store.collection.get.return_value = {
            "documents": ["content"],
            "metadatas": [{"title": "Title"}],
        }
        return store

    @pytest.fixture
    def mock_bm25_index(self):
        """Create a mock BM25 index."""
        index = MagicMock()
        index.search.return_value = [("doc1", 5.0), ("doc2", 3.0)]
        index.is_built = True
        return index

    @pytest.fixture
    def mock_query_processor(self):
        """Create a mock query processor."""
        processor = MagicMock()
        processor.process.return_value = MagicMock(
            embedding=[0.1] * 384,
            original_query="test query",
        )
        return processor

    def test_init_defaults(self):
        """Test initialization with defaults."""
        retriever = HybridRetriever()

        assert retriever.config.search_mode == "hybrid"

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = HybridConfig(search_mode="bm25")
        retriever = HybridRetriever(config=config)

        assert retriever.config.search_mode == "bm25"

    def test_vector_mode(
        self, mock_vector_store, mock_bm25_index, mock_query_processor
    ):
        """Test vector-only search mode."""
        retriever = HybridRetriever(
            config=HybridConfig(search_mode="vector"),
            vector_store=mock_vector_store,
            bm25_index=mock_bm25_index,
            query_processor=mock_query_processor,
        )

        response = retriever.retrieve("test query", top_k=5)

        # Should use vector store, not BM25
        mock_vector_store.query.assert_called_once()
        mock_bm25_index.search.assert_not_called()

        assert response.has_results

    def test_bm25_mode(
        self, mock_vector_store, mock_bm25_index, mock_query_processor
    ):
        """Test BM25-only search mode."""
        retriever = HybridRetriever(
            config=HybridConfig(search_mode="bm25"),
            vector_store=mock_vector_store,
            bm25_index=mock_bm25_index,
            query_processor=mock_query_processor,
        )

        response = retriever.retrieve("test query", top_k=5)

        # Should use BM25, not vector store for initial search
        mock_bm25_index.search.assert_called_once()

        assert response.has_results

    def test_hybrid_mode(
        self, mock_vector_store, mock_bm25_index, mock_query_processor
    ):
        """Test hybrid search mode."""
        retriever = HybridRetriever(
            config=HybridConfig(search_mode="hybrid"),
            vector_store=mock_vector_store,
            bm25_index=mock_bm25_index,
            query_processor=mock_query_processor,
        )

        response = retriever.retrieve("test query", top_k=5)

        # Should use both vector store and BM25
        mock_vector_store.query.assert_called_once()
        mock_bm25_index.search.assert_called_once()

        assert response.has_results

    def test_mode_override(
        self, mock_vector_store, mock_bm25_index, mock_query_processor
    ):
        """Test mode override in retrieve call."""
        retriever = HybridRetriever(
            config=HybridConfig(search_mode="vector"),
            vector_store=mock_vector_store,
            bm25_index=mock_bm25_index,
            query_processor=mock_query_processor,
        )

        # Override to BM25 mode
        response = retriever.retrieve("test query", mode="bm25")

        mock_bm25_index.search.assert_called_once()

    def test_compare_modes(
        self, mock_vector_store, mock_bm25_index, mock_query_processor
    ):
        """Test compare_modes method."""
        retriever = HybridRetriever(
            config=HybridConfig(),
            vector_store=mock_vector_store,
            bm25_index=mock_bm25_index,
            query_processor=mock_query_processor,
        )

        comparison = retriever.compare_modes("test query", top_k=3)

        assert "vector" in comparison
        assert "bm25" in comparison
        assert "hybrid" in comparison

    def test_distance_to_similarity(
        self, mock_vector_store, mock_bm25_index, mock_query_processor
    ):
        """Test distance to similarity conversion."""
        retriever = HybridRetriever(
            vector_store=mock_vector_store,
            bm25_index=mock_bm25_index,
            query_processor=mock_query_processor,
        )

        assert retriever._distance_to_similarity(0.0) == 1.0
        assert retriever._distance_to_similarity(0.3) == 0.7
        assert retriever._distance_to_similarity(1.0) == 0.0

    def test_response_structure(
        self, mock_vector_store, mock_bm25_index, mock_query_processor
    ):
        """Test that response has correct structure."""
        retriever = HybridRetriever(
            config=HybridConfig(search_mode="vector"),
            vector_store=mock_vector_store,
            bm25_index=mock_bm25_index,
            query_processor=mock_query_processor,
        )

        response = retriever.retrieve("test query", top_k=5)

        assert hasattr(response, "query")
        assert hasattr(response, "results")
        assert hasattr(response, "total_found")
        assert response.query == "test query"

        if response.results:
            result = response.results[0]
            assert hasattr(result, "id")
            assert hasattr(result, "content")
            assert hasattr(result, "score")
            assert hasattr(result, "metadata")
