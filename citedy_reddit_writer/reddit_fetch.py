from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from citedy_reddit_writer.config import AppConfig

log = logging.getLogger(__name__)


@dataclass
class RedditPost:
    id: str
    title: str
    subreddit: str
    score: int
    permalink: str
    url: str  # full https://www.reddit.com...
    created_utc: float


def _listing_path(listing: str, top_time: str) -> str:
    l = listing.lower()
    if l == "new":
        return "new"
    if l == "rising":
        return "rising"
    if l == "top":
        t = top_time if top_time in ("hour", "day", "week", "month", "year", "all") else "week"
        return f"top?t={t}"
    return "hot"


def fetch_subreddit_posts(
    client: httpx.Client,
    cfg: AppConfig,
    subreddit: str,
) -> list[RedditPost]:
    path = _listing_path(cfg.reddit.listing, cfg.reddit.top_time)
    limit = cfg.reddit.posts_per_subreddit
    url = f"https://www.reddit.com/r/{subreddit}/{path}.json?raw_json=1&limit={limit}"
    headers = {"User-Agent": cfg.reddit.user_agent}
    log.debug("GET %s", url)
    resp = client.get(url, headers=headers, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    children = (
        data.get("data", {}).get("children", []) if isinstance(data, dict) else []
    )
    out: list[RedditPost] = []
    for ch in children:
        if not isinstance(ch, dict) or ch.get("kind") != "t3":
            continue
        p = ch.get("data")
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", "")).removeprefix("t3_")
        title = str(p.get("title", "")).strip()
        if not pid or not title:
            continue
        sr = str(p.get("subreddit", subreddit))
        score = int(p.get("score") or 0)
        perm = str(p.get("permalink", ""))
        if not perm.startswith("/"):
            perm = "/" + perm
        full_url = f"https://www.reddit.com{perm}"
        created = float(p.get("created_utc") or 0)
        out.append(
            RedditPost(
                id=pid,
                title=title,
                subreddit=sr,
                score=score,
                permalink=perm,
                url=full_url,
                created_utc=created,
            )
        )
    return out


def fetch_all_candidates(cfg: AppConfig) -> list[RedditPost]:
    """Fetch listing posts for all configured subreddits (small delay between subs)."""
    out: list[RedditPost] = []
    with httpx.Client() as client:
        for i, sub in enumerate(cfg.subreddits):
            if i:
                time.sleep(1.2)
            try:
                posts = fetch_subreddit_posts(client, cfg, sub)
                out.extend(posts)
                log.info("r/%s: %d posts", sub, len(posts))
            except Exception as e:
                log.warning("r/%s fetch failed: %s", sub, e)
    return out
