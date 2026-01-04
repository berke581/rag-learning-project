"""Vector store implementation using ChromaDB."""

from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings

from src.vector_db.config import VectorDBConfig


class VectorStore:
    """ChromaDB-based vector store for document embeddings."""

    def __init__(self, config: Optional[VectorDBConfig] = None):
        """Initialize the vector store.

        Args:
            config: Vector DB configuration. Uses defaults if not provided.
        """
        self.config = config or VectorDBConfig.from_env()
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    @property
    def client(self) -> chromadb.PersistentClient:
        """Lazy-load the ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.config.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric},
            )
        return self._collection

    def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add documents with embeddings to the store.

        Args:
            ids: Unique identifiers for each document.
            embeddings: Vector embeddings for each document.
            documents: Text content of each document.
            metadatas: Optional metadata for each document.
        """
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def add_embedded_chunks(self, embedded_chunks: List[dict]) -> None:
        """Add embedded chunks from the Embedder.

        Args:
            embedded_chunks: List of dicts with 'id', 'embedding', 'content', 'metadata'.
        """
        ids = [chunk["id"] for chunk in embedded_chunks]
        embeddings = [chunk["embedding"] for chunk in embedded_chunks]
        documents = [chunk["content"] for chunk in embedded_chunks]
        metadatas = [chunk["metadata"] for chunk in embedded_chunks]

        self.add_documents(ids, embeddings, documents, metadatas)

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query the vector store for similar documents.

        Args:
            query_embedding: The query vector.
            n_results: Number of results to return.
            where: Optional metadata filter.

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'distances'.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        return results

    def query_text(
        self,
        query_text: str,
        embedder,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query using text (will be embedded automatically).

        Args:
            query_text: The query text to search for.
            embedder: An Embedder instance to generate the query embedding.
            n_results: Number of results to return.
            where: Optional metadata filter.

        Returns:
            List of result dicts with 'id', 'content', 'metadata', 'distance'.
        """
        query_embedding = embedder.embed_text(query_text).tolist()
        results = self.query(query_embedding, n_results, where)

        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return formatted_results

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self.client.delete_collection(self.config.collection_name)
        self._collection = None

    def clear(self) -> None:
        """Clear all documents from the collection."""
        self.delete_collection()
        # Recreate empty collection
        _ = self.collection
