from __future__ import annotations

import hashlib
import logging
import re
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from citedy_reddit_writer.config import AppConfig, FiltersConfig
    from citedy_reddit_writer.reddit_fetch import RedditPost
    from citedy_reddit_writer.state import RunState

log = logging.getLogger(__name__)


def normalize_title(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def title_hash(title: str) -> str:
    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()[:20]


def passes_keyword_filters(filters: FiltersConfig, title: str, subreddit: str) -> bool:
    hay = f"{title} r/{subreddit}".lower()
    for ex in filters.exclude_keywords:
        if ex and ex in hay:
            return False
    if filters.include_keywords:
        return any(inc and inc in hay for inc in filters.include_keywords)
    return True


def passes_score_age(post: RedditPost, filters: FiltersConfig) -> bool:
    if post.score < filters.min_score:
        return False
    now = time.time()
    age_h = (now - post.created_utc) / 3600.0
    if age_h > filters.max_age_hours:
        return False
    return True


def filter_candidates(
    cfg: AppConfig,
    posts: list[RedditPost],
    state: RunState,
    recent_titles: list[str],
) -> list[RedditPost]:
    """Filter, dedupe against state and recent article titles; sort by score desc."""
    seen_ids: set[str] = set(state.post_ids)
    seen_hashes: set[str] = set(state.title_hashes)
    recent_norm = {normalize_title(t) for t in recent_titles if t}

    kept: list[RedditPost] = []
    for p in posts:
        if p.id in seen_ids:
            continue
        th = title_hash(p.title)
        if th in seen_hashes:
            continue
        if normalize_title(p.title) in recent_norm:
            continue
        if not passes_score_age(p, cfg.filters):
            continue
        if not passes_keyword_filters(cfg.filters, p.title, p.subreddit):
            continue
        kept.append(p)

    kept.sort(key=lambda x: x.score, reverse=True)
    return kept


def format_topic(template: str, post: RedditPost) -> str:
    return (
        template.replace("{title}", post.title)
        .replace("{subreddit}", post.subreddit)
        .replace("{url}", post.url)
    )
