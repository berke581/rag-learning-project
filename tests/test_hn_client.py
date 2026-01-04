"""Tests for Hacker News API client."""

import pytest
from unittest.mock import patch, MagicMock

from src.ingestion.hn_client import HackerNewsClient, HNClientError
from src.ingestion.models import Article


class TestHackerNewsClient:
    """Tests for the HackerNewsClient class."""

    def test_init_with_defaults(self):
        """Test client initialization with default values."""
        client = HackerNewsClient()

        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.delay == 0.1

    def test_init_with_custom_values(self):
        """Test client initialization with custom values."""
        client = HackerNewsClient(timeout=60, max_retries=5, delay=0.5)

        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.delay == 0.5

    @patch("src.ingestion.hn_client.requests.get")
    def test_fetch_story_ids_success(self, mock_get):
        """Test fetching story IDs successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = [1, 2, 3, 4, 5]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = HackerNewsClient()
        ids = client.fetch_story_ids()

        assert ids == [1, 2, 3, 4, 5]
        mock_get.assert_called_once()
        assert "newstories.json" in mock_get.call_args[0][0]

    @patch("src.ingestion.hn_client.requests.get")
    def test_fetch_story_ids_with_limit(self, mock_get):
        """Test fetching story IDs with limit."""
        mock_response = MagicMock()
        mock_response.json.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = HackerNewsClient()
        ids = client.fetch_story_ids(limit=3)

        assert ids == [1, 2, 3]

    @patch("src.ingestion.hn_client.requests.get")
    def test_fetch_story_ids_topstories(self, mock_get):
        """Test fetching from topstories instead of newstories."""
        mock_response = MagicMock()
        mock_response.json.return_value = [100, 200, 300]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = HackerNewsClient()
        ids = client.fetch_story_ids(source="topstories")

        assert "topstories.json" in mock_get.call_args[0][0]

    @patch("src.ingestion.hn_client.requests.get")
    def test_fetch_item_success(self, mock_get):
        """Test fetching a single item."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "type": "story",
            "title": "Test Story",
            "text": "Content here",
            "by": "author",
            "score": 50,
            "time": 1704067200,
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = HackerNewsClient()
        item = client.fetch_item(123)

        assert item["id"] == 123
        assert item["title"] == "Test Story"
        assert "item/123.json" in mock_get.call_args[0][0]

    @patch("src.ingestion.hn_client.requests.get")
    def test_fetch_item_not_found(self, mock_get):
        """Test fetching non-existent item."""
        mock_response = MagicMock()
        mock_response.json.return_value = None
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = HackerNewsClient()
        item = client.fetch_item(99999)

        assert item is None

    @patch("src.ingestion.hn_client.requests.get")
    def test_fetch_story_ids_invalid_response(self, mock_get):
        """Test error handling for invalid response format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "invalid"}  # Not a list
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = HackerNewsClient()

        with pytest.raises(HNClientError) as exc_info:
            client.fetch_story_ids()

        assert "Expected list" in str(exc_info.value)

    @patch("src.ingestion.hn_client.requests.get")
    def test_http_error_handling(self, mock_get):
        """Test HTTP error handling."""
        from requests.exceptions import HTTPError

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        client = HackerNewsClient()

        with pytest.raises(HNClientError) as exc_info:
            client.fetch_story_ids()

        assert "HTTP error" in str(exc_info.value)

    @patch("src.ingestion.hn_client.requests.get")
    @patch("src.ingestion.hn_client.time.sleep")
    def test_timeout_retry(self, mock_sleep, mock_get):
        """Test retry logic on timeout."""
        from requests.exceptions import Timeout

        # Fail twice, succeed on third attempt
        mock_response = MagicMock()
        mock_response.json.return_value = [1, 2, 3]
        mock_response.raise_for_status = MagicMock()

        mock_get.side_effect = [
            Timeout("Connection timed out"),
            Timeout("Connection timed out"),
            mock_response,
        ]

        client = HackerNewsClient()
        ids = client.fetch_story_ids()

        assert ids == [1, 2, 3]
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # Slept between retries

    @patch("src.ingestion.hn_client.requests.get")
    def test_fetch_text_stories(self, mock_get):
        """Test fetching text stories filters correctly."""
        # Mock story IDs response
        ids_response = MagicMock()
        ids_response.json.return_value = [1, 2, 3]
        ids_response.raise_for_status = MagicMock()

        # Mock item responses
        item1 = MagicMock()
        item1.json.return_value = {
            "id": 1,
            "type": "story",
            "title": "Ask HN: Question",
            "text": "This has text content",
            "by": "user1",
            "score": 10,
            "time": 1704067200,
        }
        item1.raise_for_status = MagicMock()

        item2 = MagicMock()
        item2.json.return_value = {
            "id": 2,
            "type": "story",
            "title": "Link post",
            "url": "https://example.com",  # No text field
            "by": "user2",
            "score": 20,
            "time": 1704067200,
        }
        item2.raise_for_status = MagicMock()

        item3 = MagicMock()
        item3.json.return_value = {
            "id": 3,
            "type": "story",
            "title": "Show HN: Project",
            "text": "Here is my project",
            "by": "user3",
            "score": 30,
            "time": 1704067200,
        }
        item3.raise_for_status = MagicMock()

        mock_get.side_effect = [ids_response, item1, item2, item3]

        client = HackerNewsClient(delay=0)  # No delay for tests
        stories = client.fetch_text_stories(limit=10, show_progress=False)

        # Should only get articles with text field
        assert len(stories) == 2
        assert all(isinstance(s, Article) for s in stories)
        assert stories[0].id == 1
        assert stories[1].id == 3
