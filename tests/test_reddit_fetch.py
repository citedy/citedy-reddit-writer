from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from citedy_reddit_writer.config import load_config_from_mapping
from citedy_reddit_writer.reddit_fetch import RedditBlockedError, fetch_subreddit_posts


def _base_config() -> dict:
    return {
        "citedy": {
            "base_url": "https://www.citedy.com",
            "agent_api_key": "",
        },
        "reddit": {
            "transport": "auto",
            "user_agent": "citedy-reddit-writer/test",
            "posts_per_subreddit": 3,
            "listing": "hot",
            "top_time": "week",
        },
        "subreddits": ["SEO"],
        "filters": {
            "include_keywords": [],
            "exclude_keywords": [],
            "min_score": 0,
            "max_age_hours": 72,
        },
        "run": {
            "articles_per_run": 1,
            "max_articles_per_day": 1,
            "topic_template": "{title}",
            "language": "en",
            "size": "standard",
            "mode": "standard",
            "wait_for_completion": False,
            "auto_publish": False,
            "disable_competition": False,
            "illustrations": False,
            "audio": False,
        },
        "dedupe": {
            "state_path": "./data/state.json",
            "max_tracked_post_ids": 100,
            "sync_recent_article_titles": False,
            "recent_articles_limit": 5,
        },
        "poll": {"interval_seconds": 15, "max_wait_seconds": 60},
        "logging": {"level": "INFO"},
    }


def _listing_payload() -> dict:
    return {
        "data": {
            "children": [
                {
                    "kind": "t3",
                    "data": {
                        "id": "abc123",
                        "title": "SEO transport fallback",
                        "subreddit": "SEO",
                        "score": 42,
                        "permalink": "/r/SEO/comments/abc123/test/",
                        "created_utc": 1_700_000_000,
                    },
                }
            ]
        }
    }


class RedditFetchTransportTests(unittest.TestCase):
    def test_env_override_can_force_transport(self) -> None:
        raw = _base_config()
        raw["reddit"].pop("transport")
        with patch.dict(os.environ, {"CITEDY_REDDIT_TRANSPORT": "urllib"}, clear=False):
            cfg = load_config_from_mapping(raw)
        self.assertEqual(cfg.reddit.transport, "urllib")

    def test_auto_transport_falls_back_to_urllib_after_block(self) -> None:
        cfg = load_config_from_mapping(_base_config())
        client = Mock()

        with patch(
            "citedy_reddit_writer.reddit_fetch._fetch_payload_httpx",
            side_effect=RedditBlockedError("blocked"),
        ) as httpx_fetch, patch(
            "citedy_reddit_writer.reddit_fetch._fetch_payload_urllib",
            return_value=_listing_payload(),
        ) as urllib_fetch:
            posts = fetch_subreddit_posts(client, cfg, "SEO")

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, "abc123")
        httpx_fetch.assert_called_once()
        urllib_fetch.assert_called_once()

    def test_explicit_httpx_transport_does_not_fallback(self) -> None:
        raw = _base_config()
        raw["reddit"]["transport"] = "httpx"
        cfg = load_config_from_mapping(raw)
        client = Mock()

        with patch(
            "citedy_reddit_writer.reddit_fetch._fetch_payload_httpx",
            side_effect=RedditBlockedError("blocked"),
        ) as httpx_fetch, patch(
            "citedy_reddit_writer.reddit_fetch._fetch_payload_urllib",
        ) as urllib_fetch:
            with self.assertRaises(RedditBlockedError):
                fetch_subreddit_posts(client, cfg, "SEO")

        httpx_fetch.assert_called_once()
        urllib_fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
