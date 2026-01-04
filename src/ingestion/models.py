"""Data models for the ingestion pipeline."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class Article:
    """Represents an article from an external source (e.g., Hacker News).

    This is the primary content model used for RAG ingestion.
    """

    id: int
    title: str
    text: str
    author: str
    score: int
    time: int
    url: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Article":
        """Create an Article instance from API response data.

        Args:
            data: Raw API response dict.

        Returns:
            Article instance.
        """
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            text=data.get("text", ""),
            author=data.get("by", "unknown"),
            score=data.get("score", 0),
            time=data.get("time", 0),
            url=data.get("url"),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Article":
        """Create an Article from a dictionary (for JSON loading).

        Args:
            data: Dictionary with article data.

        Returns:
            Article instance.
        """
        return cls(
            id=data["id"],
            title=data["title"],
            text=data["text"],
            author=data["author"],
            score=data["score"],
            time=data["time"],
            url=data.get("url"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Article to a dictionary (for JSON saving).

        Returns:
            Dictionary representation.
        """
        data = {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "author": self.author,
            "score": self.score,
            "time": self.time,
        }
        if self.url:
            data["url"] = self.url
        return data

    @classmethod
    def load_from_json(cls, path: str) -> List["Article"]:
        """Load articles from a JSON file.

        Args:
            path: Path to JSON file.

        Returns:
            List of Article instances.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [cls.from_dict(item) for item in data]

    @classmethod
    def save_to_json(cls, articles: List["Article"], path: str) -> None:
        """Save articles to a JSON file.

        Args:
            articles: List of Article instances.
            path: Path to save JSON file.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = [article.to_dict() for article in articles]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @property
    def timestamp(self) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(self.time)

    @property
    def article_type(self) -> str:
        """Determine article type based on title prefix."""
        title_lower = self.title.lower()
        if title_lower.startswith("ask hn"):
            return "ask_hn"
        elif title_lower.startswith("show hn"):
            return "show_hn"
        elif title_lower.startswith("tell hn"):
            return "tell_hn"
        else:
            return "article"

    def to_document(self) -> "Document":
        """Convert Article to Document format for the RAG pipeline.

        Returns:
            Document instance ready for chunking and embedding.
        """
        # Combine title and text for full content
        content = f"{self.title}\n\n{self.text}"

        metadata = {
            "source": "hackernews",
            "source_id": self.id,
            "title": self.title,
            "author": self.author,
            "score": self.score,
            "article_type": self.article_type,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.url:
            metadata["url"] = self.url

        return Document(
            id=f"article_{self.id}",
            content=content,
            metadata=metadata,
        )

    def __str__(self) -> str:
        """String representation of the article."""
        return f"Article(id={self.id}, title='{self.title[:50]}...', score={self.score})"


@dataclass
class Document:
    """Represents a document ready for processing."""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return the length of the document content."""
        return len(self.content)


@dataclass
class Chunk:
    """Represents a chunk of text from a document."""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return the length of the chunk content."""
        return len(self.content)

    def __str__(self) -> str:
        """Return a string representation of the chunk."""
        return f"Chunk(id={self.id}, length={len(self.content)})"
