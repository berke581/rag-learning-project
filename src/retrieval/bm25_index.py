"""BM25 keyword search index for hybrid retrieval."""

import pickle
import re
from pathlib import Path
from typing import List, Optional, Tuple

from rank_bm25 import BM25Okapi


class BM25Index:
    """BM25 keyword search index.

    BM25 (Best Matching 25) is a ranking function that scores documents
    based on term frequency and inverse document frequency, with:
    - Term frequency saturation (diminishing returns)
    - Document length normalization

    This complements vector search by catching exact keyword matches
    that semantic embeddings might miss.
    """

    def __init__(self):
        """Initialize empty BM25 index."""
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self._tokenized_docs: List[List[str]] = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric chars.

        Args:
            text: Text to tokenize.

        Returns:
            List of tokens (words).
        """
        # Lowercase and split on non-word characters
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def build_index(self, documents: List[str], doc_ids: List[str]) -> None:
        """Build BM25 index from documents.

        Args:
            documents: List of document texts to index.
            doc_ids: List of document IDs (must match documents length).

        Raises:
            ValueError: If documents and doc_ids have different lengths.
        """
        if len(documents) != len(doc_ids):
            raise ValueError(
                f"documents ({len(documents)}) and doc_ids ({len(doc_ids)}) "
                "must have the same length"
            )

        self.documents = documents
        self.doc_ids = doc_ids

        # Tokenize all documents
        self._tokenized_docs = [self._tokenize(doc) for doc in documents]

        # Build BM25 index
        self.bm25 = BM25Okapi(self._tokenized_docs)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search index and return top-k results.

        Args:
            query: Search query string.
            top_k: Number of results to return.

        Returns:
            List of (doc_id, score) tuples, sorted by score descending.

        Raises:
            RuntimeError: If index has not been built.
        """
        if self.bm25 is None:
            raise RuntimeError("Index not built. Call build_index() first.")

        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices sorted by score
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = indexed_scores[:top_k]

        # Return (doc_id, score) tuples
        results = [
            (self.doc_ids[idx], score)
            for idx, score in top_indices
            if score > 0  # Filter out zero scores
        ]

        return results

    def save(self, path: str) -> None:
        """Save index to disk.

        Args:
            path: Path to save the index file.
        """
        if self.bm25 is None:
            raise RuntimeError("Index not built. Call build_index() first.")

        data = {
            "documents": self.documents,
            "doc_ids": self.doc_ids,
            "tokenized_docs": self._tokenized_docs,
        }

        # Create parent directories if needed
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str) -> None:
        """Load index from disk.

        Args:
            path: Path to the saved index file.

        Raises:
            FileNotFoundError: If index file doesn't exist.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        self.documents = data["documents"]
        self.doc_ids = data["doc_ids"]
        self._tokenized_docs = data["tokenized_docs"]

        # Rebuild BM25 from tokenized docs
        self.bm25 = BM25Okapi(self._tokenized_docs)

    @property
    def is_built(self) -> bool:
        """Check if index has been built."""
        return self.bm25 is not None

    def __len__(self) -> int:
        """Return number of documents in index."""
        return len(self.documents)
