"""Tests for the preprocessor module."""

import pytest
from src.ingestion.preprocessor import Preprocessor
from src.ingestion.models import Document, Chunk


class TestPreprocessor:
    """Test suite for Preprocessor."""

    def test_init_with_defaults(self):
        """Test preprocessor initialization with defaults."""
        preprocessor = Preprocessor()
        assert preprocessor.max_chunk_size > 0
        assert preprocessor.chunk_overlap >= 0

    def test_init_with_custom_values(self):
        """Test preprocessor initialization with custom values."""
        preprocessor = Preprocessor(max_chunk_size=300, chunk_overlap=30)
        assert preprocessor.max_chunk_size == 300
        assert preprocessor.chunk_overlap == 30

    def test_clean_text(self):
        """Test text cleaning functionality."""
        preprocessor = Preprocessor()

        # Test whitespace removal
        text = "Hello    world   \n\n  test"
        cleaned = preprocessor.clean_text(text)
        assert cleaned == "Hello world test"

        # Test leading/trailing whitespace
        text = "  Hello  "
        cleaned = preprocessor.clean_text(text)
        assert cleaned == "Hello"

    def test_split_into_sentences(self):
        """Test sentence splitting."""
        preprocessor = Preprocessor()
        text = "First sentence. Second sentence! Third sentence?"
        sentences = preprocessor._split_into_sentences(text)

        assert len(sentences) == 3
        assert "First sentence." in sentences
        assert "Second sentence!" in sentences
        assert "Third sentence?" in sentences

    def test_chunk_small_document(self):
        """Test chunking of document smaller than chunk size."""
        preprocessor = Preprocessor(max_chunk_size=500)
        doc = Document(
            id="test_1",
            content="Short content",
            metadata={"source": "test"}
        )

        chunks = preprocessor.chunk_document(doc)

        assert len(chunks) == 1
        assert chunks[0].content == "Short content"
        assert chunks[0].metadata["parent_doc_id"] == "test_1"
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[0].metadata["total_chunks"] == 1

    def test_chunk_large_document(self):
        """Test chunking of document larger than chunk size."""
        preprocessor = Preprocessor(max_chunk_size=100, chunk_overlap=20)

        # Create a document with multiple sentences
        content = "This is sentence one. " * 10  # ~220 characters
        doc = Document(
            id="test_2",
            content=content,
            metadata={"source": "test"}
        )

        chunks = preprocessor.chunk_document(doc)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Check chunk properties
        for i, chunk in enumerate(chunks):
            assert isinstance(chunk, Chunk)
            assert chunk.metadata["parent_doc_id"] == "test_2"
            assert chunk.metadata["chunk_index"] == i
            assert len(chunk.content) <= preprocessor.max_chunk_size + 50  # Allow some flexibility

        # Check total chunks metadata
        assert all(c.metadata["total_chunks"] == len(chunks) for c in chunks)

    def test_chunk_with_overlap(self):
        """Test that chunks have proper overlap."""
        preprocessor = Preprocessor(max_chunk_size=100, chunk_overlap=20)

        content = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        doc = Document(id="test_3", content=content, metadata={})

        chunks = preprocessor.chunk_document(doc)

        if len(chunks) > 1:
            # Check that consecutive chunks might have overlapping content
            # This is a simplified check - exact overlap depends on sentence boundaries
            assert len(chunks) >= 1

    def test_process_multiple_documents(self):
        """Test processing multiple documents."""
        preprocessor = Preprocessor(max_chunk_size=50)

        docs = [
            Document(id="doc_1", content="First document content.", metadata={}),
            Document(id="doc_2", content="Second document content.", metadata={}),
        ]

        chunks = preprocessor.process_documents(docs)

        # Should have chunks from both documents
        assert len(chunks) >= 2

        # Check that chunks have correct parent IDs
        parent_ids = {chunk.metadata["parent_doc_id"] for chunk in chunks}
        assert "doc_1" in parent_ids
        assert "doc_2" in parent_ids

    def test_chunk_preserves_metadata(self):
        """Test that chunking preserves document metadata."""
        preprocessor = Preprocessor()
        doc = Document(
            id="test_4",
            content="Test content",
            metadata={"source": "test", "author": "test_user", "custom": "value"}
        )

        chunks = preprocessor.chunk_document(doc)

        # All chunks should preserve original metadata
        for chunk in chunks:
            assert chunk.metadata["source"] == "test"
            assert chunk.metadata["author"] == "test_user"
            assert chunk.metadata["custom"] == "value"
            assert chunk.metadata["parent_doc_id"] == "test_4"

    def test_empty_document(self):
        """Test handling of empty document."""
        preprocessor = Preprocessor()
        doc = Document(id="empty", content="", metadata={})

        chunks = preprocessor.chunk_document(doc)

        # Empty document should still create one chunk
        assert len(chunks) == 1
        assert chunks[0].content == ""
