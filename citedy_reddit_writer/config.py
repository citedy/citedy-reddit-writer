from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from citedy_reddit_writer import __version__ as _PKG_VERSION


@dataclass
class CitedyConfig:
    base_url: str
    agent_api_key: str


@dataclass
class RedditConfig:
    transport: str
    user_agent: str
    posts_per_subreddit: int
    listing: str
    top_time: str


@dataclass
class FiltersConfig:
    include_keywords: list[str]
    exclude_keywords: list[str]
    min_score: int
    max_age_hours: int


@dataclass
class RunConfig:
    articles_per_run: int
    max_articles_per_day: int
    topic_template: str
    language: str
    size: str
    mode: str
    wait_for_completion: bool
    auto_publish: bool
    disable_competition: bool
    illustrations: bool
    audio: bool


@dataclass
class DedupeConfig:
    state_path: str
    max_tracked_post_ids: int
    sync_recent_article_titles: bool
    recent_articles_limit: int


@dataclass
class PollConfig:
    interval_seconds: int
    max_wait_seconds: int


@dataclass
class LoggingConfig:
    level: str


@dataclass
class AppConfig:
    citedy: CitedyConfig
    reddit: RedditConfig
    subreddits: list[str]
    filters: FiltersConfig
    run: RunConfig
    dedupe: DedupeConfig
    poll: PollConfig
    logging: LoggingConfig


def _normalize_reddit_transport(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"httpx", "urllib"}:
        return value
    return "auto"


def _get_str(data: dict[str, Any], *keys: str, default: str = "") -> str:
    cur: Any = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return str(cur) if cur is not None else default


def _get_int(data: dict[str, Any], *keys: str, default: int = 0) -> int:
    cur: Any = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    try:
        return int(cur)
    except (TypeError, ValueError):
        return default


def _get_bool(data: dict[str, Any], *keys: str, default: bool = False) -> bool:
    cur: Any = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    if isinstance(cur, bool):
        return cur
    if isinstance(cur, str):
        return cur.lower() in ("1", "true", "yes", "on")
    return default


def _get_str_list(data: dict[str, Any], *keys: str) -> list[str]:
    cur: Any = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return []
        cur = cur[k]
    if not isinstance(cur, list):
        return []
    return [str(x) for x in cur if x is not None]


def load_config(path: Path) -> AppConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return load_config_from_mapping(raw)


def load_config_from_mapping(raw: Any) -> AppConfig:
    """Build AppConfig from parsed YAML. Used for files and bundled defaults."""
    if not isinstance(raw, dict):
        raise ValueError("Config must be a YAML mapping")

    citedy_block = raw.get("citedy") if isinstance(raw.get("citedy"), dict) else {}
    key = _get_str(citedy_block, "agent_api_key") or os.environ.get(
        "CITEDY_AGENT_API_KEY", ""
    )
    base = _get_str(citedy_block, "base_url") or os.environ.get(
        "CITEDY_BASE_URL", "https://www.citedy.com"
    ).rstrip("/")

    reddit_block = raw.get("reddit") if isinstance(raw.get("reddit"), dict) else {}
    filters_block = raw.get("filters") if isinstance(raw.get("filters"), dict) else {}
    run_block = raw.get("run") if isinstance(raw.get("run"), dict) else {}
    dedupe_block = raw.get("dedupe") if isinstance(raw.get("dedupe"), dict) else {}
    poll_block = raw.get("poll") if isinstance(raw.get("poll"), dict) else {}
    log_block = raw.get("logging") if isinstance(raw.get("logging"), dict) else {}

    subs = raw.get("subreddits")
    if not isinstance(subs, list) or not subs:
        raise ValueError("subreddits must be a non-empty list")

    return AppConfig(
        citedy=CitedyConfig(base_url=base, agent_api_key=key),
        reddit=RedditConfig(
            transport=_normalize_reddit_transport(
                _get_str(reddit_block, "transport")
                or os.environ.get("CITEDY_REDDIT_TRANSPORT", "auto")
            ),
            user_agent=_get_str(
                reddit_block,
                "user_agent",
                default=f"citedy-reddit-writer/{_PKG_VERSION}",
            ),
            posts_per_subreddit=max(
                1, min(100, _get_int(reddit_block, "posts_per_subreddit", default=15))
            ),
            listing=_get_str(reddit_block, "listing", default="hot").lower(),
            top_time=_get_str(reddit_block, "top_time", default="week").lower(),
        ),
        subreddits=[str(s).strip().removeprefix("r/") for s in subs if s],
        filters=FiltersConfig(
            include_keywords=[k.lower() for k in _get_str_list(filters_block, "include_keywords")],
            exclude_keywords=[k.lower() for k in _get_str_list(filters_block, "exclude_keywords")],
            min_score=_get_int(filters_block, "min_score", default=5),
            max_age_hours=max(1, _get_int(filters_block, "max_age_hours", default=72)),
        ),
        run=RunConfig(
            articles_per_run=max(1, _get_int(run_block, "articles_per_run", default=1)),
            max_articles_per_day=max(1, _get_int(run_block, "max_articles_per_day", default=6)),
            topic_template=_get_str(
                run_block,
                "topic_template",
                default="Original guide inspired by Reddit: {title} (r/{subreddit})",
            ),
            language=_get_str(run_block, "language", default="en"),
            size=_get_str(run_block, "size", default="standard"),
            mode=_get_str(run_block, "mode", default="standard"),
            wait_for_completion=_get_bool(
                run_block, "wait_for_completion", default=False
            ),
            auto_publish=_get_bool(run_block, "auto_publish", default=True),
            disable_competition=_get_bool(
                run_block, "disable_competition", default=False
            ),
            illustrations=_get_bool(run_block, "illustrations", default=False),
            audio=_get_bool(run_block, "audio", default=False),
        ),
        dedupe=DedupeConfig(
            state_path=_get_str(dedupe_block, "state_path", default="./data/state.json"),
            max_tracked_post_ids=max(
                100, _get_int(dedupe_block, "max_tracked_post_ids", default=800)
            ),
            sync_recent_article_titles=_get_bool(
                dedupe_block, "sync_recent_article_titles", default=True
            ),
            recent_articles_limit=max(
                5, _get_int(dedupe_block, "recent_articles_limit", default=40)
            ),
        ),
        poll=PollConfig(
            interval_seconds=max(5, _get_int(poll_block, "interval_seconds", default=15)),
            max_wait_seconds=max(60, _get_int(poll_block, "max_wait_seconds", default=600)),
        ),
        logging=LoggingConfig(
            level=_get_str(log_block, "level", default="INFO").upper(),
        ),
    )
