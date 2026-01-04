"""CLI entry point for building the search index from fetched articles."""

import sys
from src.ingestion.models import Article
from src.ingestion.preprocessor import Preprocessor
from src.embeddings import Embedder, EmbeddingConfig
from src.vector_db import VectorStore, VectorDBConfig
from src.retrieval import BM25Index, HybridConfig


def main(input_path: str = "./data/raw/articles.json"):
    """Build the search index from fetched articles.

    This processes articles through: chunk -> embed -> store -> BM25 index.

    Args:
        input_path: Path to JSON file with fetched articles.
    """
    print("=" * 60)
    print("RAG Index Building Pipeline")
    print("=" * 60)

    # Step 1: Load articles from JSON
    print(f"\n[1/5] Loading articles from {input_path}...")
    try:
        articles = Article.load_from_json(input_path)
        print(f"      Loaded {len(articles)} articles")
    except FileNotFoundError:
        print(f"\n[ERROR] File not found: {input_path}")
        print("       Run 'rag-fetch' first to fetch articles.")
        return 1

    if len(articles) == 0:
        print("\n[ERROR] No articles found. Exiting.")
        return 1

    # Step 2: Convert to documents
    print("\n[2/5] Converting articles to documents...")
    documents = [article.to_document() for article in articles]
    print(f"      Created {len(documents)} documents")

    # Step 3: Chunk documents
    print("\n[3/5] Chunking documents...")
    preprocessor = Preprocessor()
    chunks = []
    for doc in documents:
        chunks.extend(preprocessor.chunk_document(doc))
    print(f"      Created {len(chunks)} chunks from {len(documents)} documents")
    if chunks:
        avg_size = sum(len(c.content) for c in chunks) / len(chunks)
        print(f"      Average chunk size: {avg_size:.0f} characters")

    # Step 4: Generate embeddings and store in vector database
    print("\n[4/5] Generating embeddings and storing...")
    embed_config = EmbeddingConfig.from_env()
    print(f"      Model: {embed_config.model_name}")
    embedder = Embedder(embed_config)
    print(f"      Embedding dimension: {embedder.dimension}")
    embedded_chunks = embedder.embed_chunks(chunks)
    print(f"      Generated {len(embedded_chunks)} embeddings")

    # Store in vector database
    db_config = VectorDBConfig.from_env()
    print(f"      Collection: {db_config.collection_name}")
    print(f"      Path: {db_config.persist_directory}")

    store = VectorStore(db_config)

    # Clear existing data
    old_count = store.count()
    if old_count > 0:
        print(f"      Clearing {old_count} existing documents...")
        store.clear()

    # Store new data
    store.add_embedded_chunks(embedded_chunks)
    print(f"      Stored {store.count()} documents")

    # Step 5: Build BM25 index for hybrid search
    print("\n[5/5] Building BM25 index for hybrid search...")
    hybrid_config = HybridConfig()
    bm25_index = BM25Index()

    # Extract chunk contents and IDs for BM25
    chunk_contents = [chunk["content"] for chunk in embedded_chunks]
    chunk_ids = [chunk["id"] for chunk in embedded_chunks]

    bm25_index.build_index(chunk_contents, chunk_ids)
    bm25_index.save(hybrid_config.bm25_index_path)
    print(f"      Indexed {len(bm25_index)} documents")
    print(f"      Saved to: {hybrid_config.bm25_index_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Index Building Complete!")
    print("=" * 60)
    print(f"  Articles processed: {len(articles)}")
    print(f"  Documents created:  {len(documents)}")
    print(f"  Chunks created:     {len(chunks)}")
    print(f"  Embeddings stored:  {store.count()}")
    print(f"  Embedding model:    {embed_config.model_name}")
    print(f"  Vector DB path:     {db_config.persist_directory}")
    print(f"  BM25 index path:    {hybrid_config.bm25_index_path}")

    # Demo query
    print("\n" + "-" * 60)
    print("Demo Query: 'How do I learn programming?'")
    print("-" * 60)
    results = store.query_text("How do I learn programming?", embedder, n_results=3)
    for i, result in enumerate(results, 1):
        similarity = 1 - result["distance"]
        print(f"\n[Result {i}] (similarity: {similarity:.4f})")
        print(f"  Title: {result['metadata'].get('title', 'N/A')[:50]}...")
        print(f"  Content: {result['content'][:100]}...")

    return 0


if __name__ == "__main__":
    # Allow passing input path as command line argument
    input_path = "./data/raw/articles.json"
    if len(sys.argv) > 1:
        input_path = sys.argv[1]

    sys.exit(main(input_path=input_path))
