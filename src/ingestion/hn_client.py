"""Hacker News API client for fetching articles."""

import time
from typing import List, Optional
import requests
from requests.exceptions import RequestException, Timeout, HTTPError

from src.ingestion.models import Article


class HNClientError(Exception):
    """Exception for Hacker News API client errors."""
    pass


class HackerNewsClient:
    """Client for fetching stories from Hacker News Firebase API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, timeout: int = 30, max_retries: int = 3, delay: float = 0.1):
        """Initialize the Hacker News client.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for failed requests.
            delay: Delay between requests in seconds (be polite to API).
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay

    def _make_request(self, endpoint: str) -> dict:
        """Make an HTTP request with retry logic.

        Args:
            endpoint: API endpoint (e.g., "/topstories.json").

        Returns:
            JSON response data.

        Raises:
            HNClientError: If the request fails after all retries.
        """
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.json()

            except Timeout as e:
                if attempt == self.max_retries - 1:
                    raise HNClientError(f"Request timed out after {self.max_retries} attempts: {e}")
                time.sleep(2 ** attempt)

            except HTTPError as e:
                raise HNClientError(f"HTTP error occurred: {e}")

            except RequestException as e:
                if attempt == self.max_retries - 1:
                    raise HNClientError(f"Request failed after {self.max_retries} attempts: {e}")
                time.sleep(2 ** attempt)

        raise HNClientError("Maximum retries exceeded")

    def fetch_story_ids(self, source: str = "newstories", limit: Optional[int] = None) -> List[int]:
        """Fetch story IDs from Hacker News.

        Args:
            source: Which stories to fetch ("newstories", "topstories", "beststories").
            limit: Maximum number of IDs to return (None for all).

        Returns:
            List of story IDs.
        """
        data = self._make_request(f"/{source}.json")

        if not isinstance(data, list):
            raise HNClientError(f"Expected list of story IDs, got {type(data)}")

        if limit:
            return data[:limit]
        return data

    def fetch_item(self, item_id: int) -> Optional[dict]:
        """Fetch a single item (story, comment, etc.) by ID.

        Args:
            item_id: The item ID to fetch.

        Returns:
            Item data as dict, or None if item doesn't exist.
        """
        data = self._make_request(f"/item/{item_id}.json")
        return data

    def fetch_text_stories(
        self,
        limit: int = 500,
        source: str = "newstories",
        show_progress: bool = True,
    ) -> List[Article]:
        """Fetch stories that have text content (Ask HN, Show HN, etc.).

        Args:
            limit: Target number of text articles to fetch.
            source: Which stories to fetch ("newstories", "topstories").
            show_progress: Whether to print progress.

        Returns:
            List of Article objects with text content.
        """
        if show_progress:
            print(f"Fetching article IDs from {source}...")

        # Fetch more IDs than needed since many won't have text
        story_ids = self.fetch_story_ids(source)

        if show_progress:
            print(f"Found {len(story_ids)} article IDs, fetching details...")

        articles = []
        fetched = 0

        for i, story_id in enumerate(story_ids):
            if len(articles) >= limit:
                break

            try:
                item = self.fetch_item(story_id)

                if item and item.get("type") == "story" and item.get("text"):
                    article = Article.from_api_response(item)
                    articles.append(article)

                fetched += 1

                if show_progress and fetched % 50 == 0:
                    print(f"  Fetched {fetched} items, found {len(articles)} text articles...")

                # Be polite to the API
                time.sleep(self.delay)

            except HNClientError as e:
                # Skip failed items, continue with others
                if show_progress:
                    print(f"  Warning: Failed to fetch item {story_id}: {e}")
                continue

        if show_progress:
            print(f"Completed: {len(articles)} text articles from {fetched} items")

        return articles
