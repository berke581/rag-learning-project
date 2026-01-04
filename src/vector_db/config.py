"""Configuration for the vector database module."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class VectorDBConfig:
    """Configuration for ChromaDB vector store."""

    persist_directory: str = "./data/chroma_db"
    collection_name: str = "rag_documents"
    distance_metric: str = "cosine"

    @classmethod
    def from_env(cls) -> "VectorDBConfig":
        """Create configuration from environment variables."""
        return cls(
            persist_directory=os.getenv("VECTOR_DB_PATH", "./data/chroma_db"),
            collection_name=os.getenv("VECTOR_DB_COLLECTION", "rag_documents"),
            distance_metric=os.getenv("VECTOR_DB_METRIC", "cosine"),
        )
