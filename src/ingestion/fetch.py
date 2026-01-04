"""CLI entry point for fetching articles from external sources."""

import sys
from src.ingestion.hn_client import HackerNewsClient
from src.ingestion.models import Article


def main(limit: int = 500, output_path: str = "./data/raw/articles.json"):
    """Fetch articles from Hacker News and save to JSON.

    Args:
        limit: Target number of articles to fetch.
        output_path: Path to save the fetched articles.
    """
    print("=" * 60)
    print("RAG Article Fetching Pipeline")
    print("=" * 60)

    # Step 1: Fetch stories from Hacker News
    print(f"\n[1/2] Fetching articles from Hacker News API (limit={limit})...")
    client = HackerNewsClient()
    stories = client.fetch_text_stories(limit=limit, show_progress=True)
    print(f"      Fetched {len(stories)} text articles")

    if len(stories) == 0:
        print("\n[ERROR] No articles fetched. Exiting.")
        return 1

    # Step 2: Convert to Article model and save to JSON
    print(f"\n[2/2] Saving articles to {output_path}...")
    articles = [
        Article(
            id=story.id,
            title=story.title,
            text=story.text,
            author=story.author,
            score=story.score,
            time=story.time,
            url=story.url,
        )
        for story in stories
    ]
    Article.save_to_json(articles, output_path)
    print(f"      Saved {len(articles)} articles")

    # Summary
    print("\n" + "=" * 60)
    print("Fetching Complete!")
    print("=" * 60)
    print(f"  Articles fetched: {len(articles)}")
    print(f"  Output file:      {output_path}")

    # Show sample
    print("\n" + "-" * 60)
    print("Sample Articles Fetched:")
    print("-" * 60)
    for article in articles[:3]:
        print(f"\n  [{article.article_type.upper()}] {article.title[:60]}...")
        print(f"  Score: {article.score} | Author: {article.author}")

    print("\n" + "-" * 60)
    print("Next step: Run 'rag-process' to build the search index.")
    print("-" * 60)

    return 0


if __name__ == "__main__":
    # Parse command line arguments
    limit = 500
    output_path = "./data/raw/articles.json"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                print(f"Invalid limit: {args[i + 1]}, using default 500")
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            # Assume first positional arg is limit
            try:
                limit = int(args[i])
            except ValueError:
                pass
            i += 1

    sys.exit(main(limit=limit, output_path=output_path))
