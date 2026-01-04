"""Configuration for the embeddings module."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""

    model_name: str = "all-MiniLM-L6-v2"
    cache_dir: str = "./data/models"
    batch_size: int = 32
    show_progress: bool = True
    normalize_embeddings: bool = True

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create configuration from environment variables."""
        return cls(
            model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            cache_dir=os.getenv("MODEL_CACHE_DIR", "./data/models"),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
            show_progress=os.getenv("EMBEDDING_SHOW_PROGRESS", "true").lower() == "true",
            normalize_embeddings=os.getenv("EMBEDDING_NORMALIZE", "true").lower() == "true",
        )
