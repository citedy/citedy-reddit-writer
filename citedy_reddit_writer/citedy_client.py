from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from citedy_reddit_writer.config import AppConfig, PollConfig

log = logging.getLogger(__name__)

TERMINAL_SUCCESS = frozenset({"published", "generated", "publishing"})
TERMINAL_FAILURE = frozenset({"failed"})


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def fetch_recent_article_titles(
    client: httpx.Client,
    cfg: AppConfig,
    limit: int,
) -> list[str]:
    url = f"{cfg.citedy.base_url}/api/agent/articles"
    r = client.get(
        url,
        headers=_headers(cfg.citedy.agent_api_key),
        params={"limit": min(100, max(1, limit))},
        timeout=60.0,
    )
    r.raise_for_status()
    data = r.json()
    articles = data.get("articles") if isinstance(data, dict) else None
    if not isinstance(articles, list):
        return []
    titles: list[str] = []
    for a in articles:
        if isinstance(a, dict) and a.get("title"):
            titles.append(str(a["title"]))
    return titles


def post_autopilot(
    client: httpx.Client,
    cfg: AppConfig,
    topic: str,
    source_urls: list[str],
) -> tuple[int, dict[str, Any]]:
    url = f"{cfg.citedy.base_url}/api/agent/autopilot"
    body: dict[str, Any] = {
        "topic": topic,
        "source_urls": source_urls[:3],
        "language": cfg.run.language,
        "size": cfg.run.size,
        "mode": cfg.run.mode,
        "wait_for_completion": cfg.run.wait_for_completion,
        "auto_publish": cfg.run.auto_publish,
        "disable_competition": cfg.run.disable_competition,
        "illustrations": cfg.run.illustrations,
        "audio": cfg.run.audio,
    }
    log.info("POST %s (topic=%r, urls=%s)", url, topic[:80], len(source_urls))
    r = client.post(
        url,
        headers=_headers(cfg.citedy.agent_api_key),
        json=body,
        timeout=120.0,
    )
    try:
        payload = r.json() if r.content else {}
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    return r.status_code, payload


def extract_job_id(payload: dict[str, Any]) -> str | None:
    jid = payload.get("id") or payload.get("jobId")
    if isinstance(jid, str) and jid:
        return jid
    return None


def extract_sync_article_id(payload: dict[str, Any]) -> str | None:
    aid = payload.get("article_id")
    if isinstance(aid, str) and aid:
        return aid
    return None


def poll_article_job(
    client: httpx.Client,
    cfg: AppConfig,
    job_id: str,
    poll: PollConfig,
) -> dict[str, Any]:
    url = f"{cfg.citedy.base_url}/api/agent/articles/{job_id}"
    deadline = time.monotonic() + poll.max_wait_seconds
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        r = client.get(
            url,
            headers=_headers(cfg.citedy.agent_api_key),
            timeout=60.0,
        )
        r.raise_for_status()
        last = r.json()
        if not isinstance(last, dict):
            raise RuntimeError("Invalid poll response")
        status = last.get("status")
        if status in TERMINAL_FAILURE:
            return last
        if status in TERMINAL_SUCCESS or last.get("article_id"):
            return last
        if status != "processing" and not last.get("queued"):
            return last
        log.info("Job %s still processing (%s)", job_id, last.get("message", ""))
        time.sleep(poll.interval_seconds)
    raise TimeoutError(f"Poll timeout for job {job_id}: last={last!r}")


def is_poll_success(payload: dict[str, Any]) -> bool:
    st = payload.get("status")
    if st in TERMINAL_FAILURE:
        return False
    if st in TERMINAL_SUCCESS or payload.get("article_id"):
        return True
    return False
