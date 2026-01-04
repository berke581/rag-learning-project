"""Tests for the data models module."""

import pytest
import tempfile
import os
from datetime import datetime

from src.ingestion.models import Article, Document, Chunk


class TestArticle:
    """Tests for the Article model."""

    def test_article_creation(self):
        """Test creating an Article instance."""
        article = Article(
            id=123,
            title="Ask HN: How do I learn programming?",
            text="I want to learn Python and build projects.",
            author="testuser",
            score=150,
            time=1704067200,
        )

        assert article.id == 123
        assert article.title == "Ask HN: How do I learn programming?"
        assert article.text == "I want to learn Python and build projects."
        assert article.author == "testuser"
        assert article.score == 150
        assert article.url is None

    def test_from_api_response(self):
        """Test creating Article from API response."""
        api_data = {
            "id": 456,
            "type": "story",
            "title": "Show HN: My new project",
            "text": "Check out what I built!",
            "by": "developer",
            "score": 75,
            "time": 1704153600,
            "url": "https://example.com",
        }

        article = Article.from_api_response(api_data)

        assert article.id == 456
        assert article.title == "Show HN: My new project"
        assert article.text == "Check out what I built!"
        assert article.author == "developer"
        assert article.score == 75
        assert article.url == "https://example.com"

    def test_from_api_response_missing_fields(self):
        """Test creating Article with missing optional fields."""
        api_data = {
            "id": 789,
            "type": "story",
        }

        article = Article.from_api_response(api_data)

        assert article.id == 789
        assert article.title == ""
        assert article.text == ""
        assert article.author == "unknown"
        assert article.score == 0
        assert article.url is None

    def test_timestamp_property(self):
        """Test timestamp conversion."""
        article = Article(
            id=1,
            title="Test",
            text="Content",
            author="user",
            score=10,
            time=1704067200,  # 2024-01-01 00:00:00 UTC
        )

        ts = article.timestamp
        assert isinstance(ts, datetime)
        assert ts.year == 2024
        assert ts.month == 1
        assert ts.day == 1

    def test_article_type_ask_hn(self):
        """Test article type detection for Ask HN."""
        article = Article(
            id=1, title="Ask HN: Best practices?", text="", author="", score=0, time=0
        )
        assert article.article_type == "ask_hn"

    def test_article_type_show_hn(self):
        """Test article type detection for Show HN."""
        article = Article(
            id=1, title="Show HN: My project", text="", author="", score=0, time=0
        )
        assert article.article_type == "show_hn"

    def test_article_type_tell_hn(self):
        """Test article type detection for Tell HN."""
        article = Article(
            id=1, title="Tell HN: Important news", text="", author="", score=0, time=0
        )
        assert article.article_type == "tell_hn"

    def test_article_type_regular(self):
        """Test article type detection for regular articles."""
        article = Article(
            id=1, title="Regular article title", text="", author="", score=0, time=0
        )
        assert article.article_type == "article"

    def test_to_document(self):
        """Test conversion to Document."""
        article = Article(
            id=123,
            title="Ask HN: Learning Python",
            text="What resources do you recommend?",
            author="learner",
            score=50,
            time=1704067200,
            url="https://example.com",
        )

        doc = article.to_document()

        assert isinstance(doc, Document)
        assert doc.id == "article_123"
        assert "Ask HN: Learning Python" in doc.content
        assert "What resources do you recommend?" in doc.content
        assert doc.metadata["source"] == "hackernews"
        assert doc.metadata["source_id"] == 123
        assert doc.metadata["title"] == "Ask HN: Learning Python"
        assert doc.metadata["author"] == "learner"
        assert doc.metadata["score"] == 50
        assert doc.metadata["article_type"] == "ask_hn"
        assert doc.metadata["url"] == "https://example.com"

    def test_to_document_without_url(self):
        """Test conversion to Document without URL."""
        article = Article(
            id=456,
            title="Show HN: Project",
            text="Details here",
            author="dev",
            score=100,
            time=1704067200,
        )

        doc = article.to_document()

        assert "url" not in doc.metadata

    def test_str_representation(self):
        """Test string representation."""
        article = Article(
            id=1,
            title="A very long title that should be truncated in the string representation",
            text="Content",
            author="user",
            score=42,
            time=0,
        )

        s = str(article)
        assert "Article" in s
        assert "id=1" in s
        assert "score=42" in s
        assert "..." in s  # Truncated title

    def test_to_dict(self):
        """Test converting Article to dictionary."""
        article = Article(
            id=123,
            title="Test Title",
            text="Test content",
            author="testuser",
            score=50,
            time=1704067200,
            url="https://example.com",
        )

        data = article.to_dict()

        assert data["id"] == 123
        assert data["title"] == "Test Title"
        assert data["text"] == "Test content"
        assert data["author"] == "testuser"
        assert data["score"] == 50
        assert data["time"] == 1704067200
        assert data["url"] == "https://example.com"

    def test_to_dict_without_url(self):
        """Test converting Article without URL to dictionary."""
        article = Article(
            id=123,
            title="Test",
            text="Content",
            author="user",
            score=10,
            time=1704067200,
        )

        data = article.to_dict()

        assert "url" not in data

    def test_from_dict(self):
        """Test creating Article from dictionary."""
        data = {
            "id": 456,
            "title": "Dict Title",
            "text": "Dict content",
            "author": "dictuser",
            "score": 75,
            "time": 1704153600,
            "url": "https://dict.example.com",
        }

        article = Article.from_dict(data)

        assert article.id == 456
        assert article.title == "Dict Title"
        assert article.text == "Dict content"
        assert article.author == "dictuser"
        assert article.score == 75
        assert article.time == 1704153600
        assert article.url == "https://dict.example.com"

    def test_save_and_load_json(self):
        """Test saving and loading articles to/from JSON."""
        articles = [
            Article(id=1, title="First", text="Content 1", author="a", score=10, time=1000),
            Article(id=2, title="Second", text="Content 2", author="b", score=20, time=2000),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "articles.json")
            Article.save_to_json(articles, path)

            loaded = Article.load_from_json(path)

            assert len(loaded) == 2
            assert loaded[0].id == 1
            assert loaded[0].title == "First"
            assert loaded[1].id == 2
            assert loaded[1].title == "Second"


class TestDocument:
    """Test suite for Document model."""

    def test_document_creation(self):
        """Test creating a Document instance."""
        doc = Document(
            id="doc_1",
            content="Test content",
            metadata={"source": "test"}
        )

        assert doc.id == "doc_1"
        assert doc.content == "Test content"
        assert doc.metadata["source"] == "test"

    def test_document_length(self):
        """Test Document length calculation."""
        doc = Document(id="doc_1", content="Hello world")

        assert len(doc) == 11

    def test_document_default_metadata(self):
        """Test Document with default metadata."""
        doc = Document(id="doc_1", content="Content")

        assert isinstance(doc.metadata, dict)
        assert len(doc.metadata) == 0


class TestChunk:
    """Test suite for Chunk model."""

    def test_chunk_creation(self):
        """Test creating a Chunk instance."""
        chunk = Chunk(
            id="chunk_1",
            content="Chunk content",
            metadata={"parent_doc_id": "doc_1"}
        )

        assert chunk.id == "chunk_1"
        assert chunk.content == "Chunk content"
        assert chunk.metadata["parent_doc_id"] == "doc_1"

    def test_chunk_length(self):
        """Test Chunk length calculation."""
        chunk = Chunk(id="chunk_1", content="Test")

        assert len(chunk) == 4

    def test_chunk_string_representation(self):
        """Test Chunk string representation."""
        chunk = Chunk(id="chunk_1", content="Hello world")
        string_repr = str(chunk)

        assert "chunk_1" in string_repr
        assert "11" in string_repr  # length

    def test_chunk_default_metadata(self):
        """Test Chunk with default metadata."""
        chunk = Chunk(id="chunk_1", content="Content")

        assert isinstance(chunk.metadata, dict)
        assert len(chunk.metadata) == 0
