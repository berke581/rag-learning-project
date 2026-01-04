"""CLI for interactive querying of the RAG system."""

import sys
from src.retrieval import HybridRetriever, HybridConfig, RetrievalConfig


def print_result(result, index: int) -> None:
    """Print a single retrieval result."""
    print(f"\n{'='*60}")
    print(f"Result {index} | Score: {result.score:.4f}")
    print(f"{'='*60}")
    print(f"ID: {result.id}")

    if result.metadata:
        title = result.metadata.get("title", "N/A")
        source = result.metadata.get("source", "N/A")
        # Handle Unicode errors for Windows console
        try:
            print(f"Title: {title}")
        except UnicodeEncodeError:
            print(f"Title: {title.encode('ascii', 'replace').decode('ascii')}")
        print(f"Source: {source}")

    # Handle Unicode errors for Windows console
    try:
        print(f"\nContent:\n{result.content}")
    except UnicodeEncodeError:
        print(f"\nContent:\n{result.content.encode('ascii', 'replace').decode('ascii')}")


def interactive_mode(retriever: HybridRetriever) -> None:
    """Run interactive query mode."""
    print("\n" + "="*60)
    print("RAG Interactive Query (Hybrid Search)")
    print("="*60)
    print("Type your query and press Enter.")
    print("Commands: 'quit' or 'exit' to stop, 'help' for options")
    print(f"Search mode: {retriever.config.search_mode.upper()}")
    print("="*60)

    while True:
        try:
            query = input("\nQuery> ").strip()

            if not query:
                continue

            if query.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if query.lower() == "help":
                print("\nOptions:")
                print("  k=N      - Set number of results (e.g., k=3)")
                print("  t=N      - Set threshold (e.g., t=0.5)")
                print("  mode=X   - Set search mode: vector, bm25, hybrid")
                print("  quit     - Exit the program")
                print(f"\nCurrent mode: {retriever.config.search_mode}")
                continue

            # Parse options from query
            top_k = retriever.config.top_k
            threshold = retriever.config.similarity_threshold
            mode = None

            # Check for k= option
            if "k=" in query:
                parts = query.split()
                for part in parts:
                    if part.startswith("k="):
                        try:
                            top_k = int(part[2:])
                            query = query.replace(part, "").strip()
                        except ValueError:
                            pass

            # Check for t= option
            if "t=" in query:
                parts = query.split()
                for part in parts:
                    if part.startswith("t="):
                        try:
                            threshold = float(part[2:])
                            query = query.replace(part, "").strip()
                        except ValueError:
                            pass

            # Check for mode= option
            if "mode=" in query:
                parts = query.split()
                for part in parts:
                    if part.startswith("mode="):
                        mode_value = part[5:].lower()
                        if mode_value in ["vector", "bm25", "hybrid"]:
                            mode = mode_value
                            query = query.replace(part, "").strip()
                        else:
                            print(f"Invalid mode '{mode_value}'. Use: vector, bm25, or hybrid")
                            continue

            if not query:
                print("Please enter a query.")
                continue

            # Perform retrieval
            mode_str = f", mode={mode}" if mode else ""
            print(f"\nSearching for: '{query}' (k={top_k}, threshold={threshold}{mode_str})...")
            response = retriever.retrieve(query, top_k=top_k, threshold=threshold, mode=mode)

            if not response.has_results:
                print("\nNo results found above the similarity threshold.")
                continue

            print(f"\nFound {response.total_found} results:")

            for i, result in enumerate(response.results, 1):
                print_result(result, i)

            # Show context summary
            print(f"\n{'-'*60}")
            print("Context for LLM (combined):")
            print(f"{'-'*60}")
            print(response.get_context_with_sources()[:500] + "...")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def single_query(retriever: HybridRetriever, query: str, top_k: int = 5) -> None:
    """Run a single query and print results."""
    print(f"\nQuery: {query}")
    print(f"Retrieving top {top_k} results...")

    response = retriever.retrieve(query, top_k=top_k)

    if not response.has_results:
        print("\nNo results found.")
        return

    print(f"\nFound {response.total_found} results:")
    for i, result in enumerate(response.results, 1):
        print_result(result, i)


def main():
    """Main entry point."""
    print("Initializing hybrid retriever (BM25 + Vector)...")
    hybrid_config = HybridConfig(search_mode="hybrid")
    retrieval_config = RetrievalConfig.from_env()
    retriever = HybridRetriever(
        config=hybrid_config,
        retrieval_config=retrieval_config,
    )

    # Check if query provided as argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        single_query(retriever, query)
    else:
        interactive_mode(retriever)


if __name__ == "__main__":
    main()
