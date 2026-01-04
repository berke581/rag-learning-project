"""Configuration module for loading environment variables."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class IngestionConfig:
    """Configuration for data ingestion."""

    # Chunking Configuration
    max_chunk_size: int = int(os.getenv("MAX_CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_chunk_size <= 0:
            raise ValueError("MAX_CHUNK_SIZE must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP must be non-negative")
        if self.chunk_overlap >= self.max_chunk_size:
            raise ValueError("CHUNK_OVERLAP must be less than MAX_CHUNK_SIZE")


# Global configuration instance
config = IngestionConfig()
