"""Configuration for the retrieval module."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RetrievalConfig:
    """Configuration for retrieval operations."""

    # Number of results to retrieve
    top_k: int = 5

    # Similarity threshold (0-1 for cosine, results below this are filtered)
    similarity_threshold: float = 0.0

    @classmethod
    def from_env(cls) -> "RetrievalConfig":
        """Create configuration from environment variables."""
        return cls(
            top_k=int(os.getenv("RETRIEVAL_K", "5")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.0")),
        )
