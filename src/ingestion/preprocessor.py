"""Text preprocessing and chunking utilities."""

import re
from typing import List

from src.ingestion.config import config
from src.ingestion.models import Document, Chunk


class Preprocessor:
    """Handles text cleaning and chunking for documents."""

    def __init__(self, max_chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize the preprocessor.

        Args:
            max_chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.max_chunk_size = max_chunk_size or config.max_chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Split a document into overlapping chunks.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        # Clean the text first
        clean_content = self.clean_text(document.content)

        # If document is smaller than chunk size, return as single chunk
        if len(clean_content) <= self.max_chunk_size:
            chunk = Chunk(
                id=f"{document.id}_chunk_0",
                content=clean_content,
                metadata={
                    **document.metadata,
                    "parent_doc_id": document.id,
                    "chunk_index": 0,
                    "total_chunks": 1,
                },
            )
            return [chunk]

        # Split into sentences for better chunking
        sentences = self._split_into_sentences(clean_content)

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_len = len(sentence) + 1  # +1 for space

            # If single sentence exceeds max size, split it
            if sentence_len > self.max_chunk_size:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split long sentence into chunks
                for i in range(0, len(sentence), self.max_chunk_size - self.chunk_overlap):
                    chunk_text = sentence[i:i + self.max_chunk_size]
                    chunks.append(chunk_text)
                continue

            # If adding sentence exceeds max size, start new chunk
            if current_size + sentence_len > self.max_chunk_size:
                chunks.append(" ".join(current_chunk))

                # Keep some sentences for overlap
                overlap_text = " ".join(current_chunk)
                if len(overlap_text) > self.chunk_overlap:
                    # Start new chunk with overlapping content
                    overlap_sentences = []
                    overlap_size = 0
                    for s in reversed(current_chunk):
                        if overlap_size + len(s) + 1 <= self.chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_size += len(s) + 1
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_len

        # Add remaining content
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Convert to Chunk objects
        chunk_objects = []
        for idx, chunk_text in enumerate(chunks):
            chunk = Chunk(
                id=f"{document.id}_chunk_{idx}",
                content=chunk_text,
                metadata={
                    **document.metadata,
                    "parent_doc_id": document.id,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                },
            )
            chunk_objects.append(chunk)

        return chunk_objects

    def process_documents(self, documents: List[Document]) -> List[Chunk]:
        """
        Process multiple documents into chunks.

        Args:
            documents: List of documents to process

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks
