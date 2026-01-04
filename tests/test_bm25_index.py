"""Tests for BM25 keyword search index."""

import os
import tempfile
import pytest

from src.retrieval.bm25_index import BM25Index


class TestBM25Index:
    """Tests for the BM25Index class."""

    def test_init(self):
        """Test BM25Index initialization."""
        index = BM25Index()

        assert index.bm25 is None
        assert index.documents == []
        assert index.doc_ids == []
        assert not index.is_built

    def test_build_index(self):
        """Test building the index."""
        index = BM25Index()

        documents = [
            "The quick brown fox jumps over the lazy dog",
            "A fast brown cat runs past the sleeping dog",
            "Python programming language tutorial",
        ]
        doc_ids = ["doc1", "doc2", "doc3"]

        index.build_index(documents, doc_ids)

        assert index.is_built
        assert len(index) == 3
        assert index.documents == documents
        assert index.doc_ids == doc_ids

    def test_build_index_length_mismatch(self):
        """Test error when documents and doc_ids have different lengths."""
        index = BM25Index()

        with pytest.raises(ValueError) as exc_info:
            index.build_index(["doc1", "doc2"], ["id1"])

        assert "same length" in str(exc_info.value)

    def test_search_basic(self):
        """Test basic search functionality."""
        index = BM25Index()

        documents = [
            "The quick brown fox jumps over the lazy dog",
            "Python programming language tutorial",
            "Machine learning with Python",
        ]
        doc_ids = ["doc1", "doc2", "doc3"]

        index.build_index(documents, doc_ids)

        # Search for "Python" should return doc2 and doc3
        results = index.search("Python", top_k=3)

        assert len(results) == 2
        result_ids = [r[0] for r in results]
        assert "doc2" in result_ids
        assert "doc3" in result_ids

    def test_search_exact_match_ranks_higher(self):
        """Test that exact keyword matches rank higher."""
        index = BM25Index()

        documents = [
            "Regex tester, diff checker, image utilities",
            "A collection of various developer tools",
            "Programming resources and tutorials",
        ]
        doc_ids = ["doc1", "doc2", "doc3"]

        index.build_index(documents, doc_ids)

        # Search for exact phrase from doc1
        results = index.search("regex tester diff checker", top_k=3)

        # doc1 should be the top result
        assert len(results) >= 1
        assert results[0][0] == "doc1"

    def test_search_empty_query(self):
        """Test search with empty query."""
        index = BM25Index()
        index.build_index(["document one", "document two"], ["id1", "id2"])

        results = index.search("", top_k=5)
        assert results == []

    def test_search_no_match(self):
        """Test search with query that doesn't match any documents."""
        index = BM25Index()
        index.build_index(
            ["apple banana cherry", "dog cat mouse"],
            ["id1", "id2"]
        )

        results = index.search("xyz123nonexistent", top_k=5)
        assert results == []

    def test_search_not_built(self):
        """Test error when searching without building index."""
        index = BM25Index()

        with pytest.raises(RuntimeError) as exc_info:
            index.search("test")

        assert "not built" in str(exc_info.value)

    def test_tokenize(self):
        """Test tokenization."""
        index = BM25Index()

        tokens = index._tokenize("Hello, World! How are you?")

        assert tokens == ["hello", "world", "how", "are", "you"]

    def test_tokenize_special_chars(self):
        """Test tokenization with special characters."""
        index = BM25Index()

        tokens = index._tokenize("user@example.com visited https://example.com")

        # Should split on special characters
        assert "user" in tokens
        assert "example" in tokens
        assert "com" in tokens

    def test_save_and_load(self):
        """Test saving and loading index."""
        index = BM25Index()

        # Use distinct documents to ensure good BM25 scores
        documents = [
            "zebra animal stripes africa wildlife",
            "elephant animal trunk africa wildlife",
            "python programming language coding software",
            "javascript programming language coding software",
        ]
        doc_ids = ["doc1", "doc2", "doc3", "doc4"]

        index.build_index(documents, doc_ids)

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            temp_path = f.name

        try:
            index.save(temp_path)

            # Load into new index
            new_index = BM25Index()
            new_index.load(temp_path)

            assert new_index.is_built
            assert len(new_index) == 4
            assert new_index.documents == documents
            assert new_index.doc_ids == doc_ids

            # Verify search works - search for unique term "zebra"
            results = new_index.search("zebra", top_k=4)
            assert len(results) >= 1
            assert results[0][0] == "doc1"

        finally:
            os.unlink(temp_path)

    def test_save_not_built(self):
        """Test error when saving without building index."""
        index = BM25Index()

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError) as exc_info:
                index.save(temp_path)

            assert "not built" in str(exc_info.value)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_nonexistent(self):
        """Test error when loading from nonexistent file."""
        index = BM25Index()

        with pytest.raises(FileNotFoundError):
            index.load("/nonexistent/path/index.pkl")

    def test_top_k_limit(self):
        """Test that top_k limits results."""
        index = BM25Index()

        documents = [f"document {i} with keyword" for i in range(10)]
        doc_ids = [f"doc{i}" for i in range(10)]

        index.build_index(documents, doc_ids)

        results = index.search("keyword", top_k=3)
        assert len(results) == 3

    def test_case_insensitive(self):
        """Test that search is case insensitive."""
        index = BM25Index()

        # Need multiple docs for BM25 IDF to work properly
        documents = [
            "Python Programming Guide for developers",
            "JavaScript tutorial for web development",
            "Ruby on Rails framework guide",
            "Go language programming basics",
        ]
        doc_ids = ["doc1", "doc2", "doc3", "doc4"]

        index.build_index(documents, doc_ids)

        # All case variations should match and return doc1
        results1 = index.search("python", top_k=4)
        results2 = index.search("PYTHON", top_k=4)
        results3 = index.search("Python", top_k=4)

        assert len(results1) >= 1
        assert len(results2) >= 1
        assert len(results3) >= 1

        # All should return doc1 as top result
        assert results1[0][0] == "doc1"
        assert results2[0][0] == "doc1"
        assert results3[0][0] == "doc1"
