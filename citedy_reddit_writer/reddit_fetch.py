from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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


class RedditFetchError(RuntimeError):
    """Generic Reddit listing fetch failure."""


class RedditBlockedError(RedditFetchError):
    """Reddit returned a block page or similar anti-bot response."""


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


def _listing_url(cfg: AppConfig, subreddit: str) -> str:
    path = _listing_path(cfg.reddit.listing, cfg.reddit.top_time)
    limit = cfg.reddit.posts_per_subreddit
    return f"https://www.reddit.com/r/{subreddit}/{path}.json?raw_json=1&limit={limit}"


def _looks_like_block(status_code: int, content_type: str, body_text: str) -> bool:
    lower_body = body_text.lower()
    lower_type = content_type.lower()
    if status_code == 403 and "blocked" in lower_body:
        return True
    if "text/html" in lower_type and "<body" in lower_body and "blocked" in lower_body:
        return True
    return False


def _response_preview(body_text: str) -> str:
    return body_text[:160].replace("\n", " ").strip()


def _parse_listing_payload(data: object, subreddit: str) -> list[RedditPost]:
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


def _fetch_payload_httpx(
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
) -> object:
    resp = client.get(url, headers=headers, timeout=30.0)
    body_text = resp.text
    if _looks_like_block(resp.status_code, resp.headers.get("Content-Type", ""), body_text):
        raise RedditBlockedError(
            f"Client error '{resp.status_code} Blocked' for url '{url}'"
        )
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RedditFetchError(str(exc)) from exc
    try:
        return resp.json()
    except ValueError as exc:
        raise RedditFetchError(
            f"Invalid JSON from {url}: {_response_preview(body_text)}"
        ) from exc


def _fetch_payload_urllib(url: str, headers: dict[str, str]) -> object:
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30.0) as resp:
            body = resp.read()
            status_code = getattr(resp, "status", 200)
            content_type = resp.headers.get("Content-Type", "")
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", "ignore")
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        if _looks_like_block(exc.code, content_type, body_text):
            raise RedditBlockedError(
                f"HTTP {exc.code} blocked for url '{url}'"
            ) from exc
        raise RedditFetchError(f"HTTP {exc.code} for url '{url}'") from exc
    except URLError as exc:
        raise RedditFetchError(f"URL error for '{url}': {exc}") from exc

    body_text = body.decode("utf-8", "ignore")
    if _looks_like_block(status_code, content_type, body_text):
        raise RedditBlockedError(f"HTTP {status_code} blocked for url '{url}'")
    try:
        return json.loads(body_text)
    except ValueError as exc:
        raise RedditFetchError(
            f"Invalid JSON from {url}: {_response_preview(body_text)}"
        ) from exc


def _transport_order(configured_transport: str) -> tuple[str, ...]:
    if configured_transport == "httpx":
        return ("httpx",)
    if configured_transport == "urllib":
        return ("urllib",)
    return ("httpx", "urllib")


def fetch_subreddit_posts(
    client: httpx.Client,
    cfg: AppConfig,
    subreddit: str,
) -> list[RedditPost]:
    url = _listing_url(cfg, subreddit)
    headers = {
        "User-Agent": cfg.reddit.user_agent,
        "Accept": "application/json",
    }
    log.debug("GET %s", url)

    last_error: Exception | None = None
    transports = _transport_order(cfg.reddit.transport)
    for index, transport in enumerate(transports):
        try:
            if transport == "httpx":
                payload = _fetch_payload_httpx(client, url, headers)
            else:
                payload = _fetch_payload_urllib(url, headers)
            if index:
                log.info("r/%s: Reddit fetch succeeded via %s", subreddit, transport)
            return _parse_listing_payload(payload, subreddit)
        except RedditBlockedError as exc:
            last_error = exc
            if index + 1 >= len(transports):
                raise
            log.warning(
                "r/%s %s blocked by Reddit, retrying via %s",
                subreddit,
                transport,
                transports[index + 1],
            )
        except RedditFetchError as exc:
            last_error = exc
            if index + 1 >= len(transports):
                raise
            log.warning(
                "r/%s %s fetch failed (%s), retrying via %s",
                subreddit,
                transport,
                exc,
                transports[index + 1],
            )

    if last_error is not None:
        raise last_error
    raise RedditFetchError(f"Failed to fetch subreddit listing for r/{subreddit}")


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
