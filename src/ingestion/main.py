"""CLI entry point for the complete RAG ingestion pipeline.

This is a convenience wrapper that runs both fetch and process stages.
For more control, use 'rag-fetch' and 'rag-process' separately.
"""

import sys
from src.ingestion.fetch import main as fetch_main
from src.indexing.process import main as process_main


def main(limit: int = 500):
    """Run the complete ingestion pipeline: fetch -> process.

    Args:
        limit: Target number of articles to fetch.
    """
    output_path = "./data/raw/articles.json"

    print("=" * 60)
    print("RAG Complete Ingestion Pipeline")
    print("=" * 60)
    print("\nThis will run: fetch -> process")
    print("For more control, use 'rag-fetch' and 'rag-process' separately.\n")

    # Step 1: Fetch articles
    print("=" * 60)
    print("STAGE 1: FETCHING")
    print("=" * 60)
    result = fetch_main(limit=limit, output_path=output_path)
    if result != 0:
        return result

    print("\n")

    # Step 2: Process and build index
    print("=" * 60)
    print("STAGE 2: PROCESSING")
    print("=" * 60)
    result = process_main(input_path=output_path)
    if result != 0:
        return result

    print("\n" + "=" * 60)
    print("COMPLETE PIPELINE FINISHED!")
    print("=" * 60)
    print("\nYou can now query the system with 'rag-query'.")

    return 0


if __name__ == "__main__":
    # Allow passing limit as command line argument
    limit = 500
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Invalid limit: {sys.argv[1]}, using default 500")

    sys.exit(main(limit=limit))
