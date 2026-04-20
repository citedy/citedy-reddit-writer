from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from importlib import resources
from pathlib import Path

import httpx
import yaml

from citedy_reddit_writer.citedy_client import (
    extract_job_id,
    extract_sync_article_id,
    fetch_recent_article_titles,
    is_poll_success,
    poll_article_job,
    post_autopilot,
)
from citedy_reddit_writer.config import AppConfig, load_config, load_config_from_mapping
from citedy_reddit_writer.filter_dedupe import (
    filter_candidates,
    format_topic,
    title_hash,
)
from citedy_reddit_writer.reddit_fetch import fetch_all_candidates
from citedy_reddit_writer.state import (
    RunState,
    daily_count,
    increment_daily,
    load_state,
    save_state,
    trim_state,
)


def _resolve_path(base: Path, p: str) -> Path:
    path = Path(p)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _resolve_config_and_base(
    config_arg: str,
) -> tuple[AppConfig, Path, str] | None:
    """Load AppConfig; base dir anchors relative paths (state_path). Returns None on failure."""
    requested = Path(config_arg).expanduser().resolve()

    if requested.is_file():
        return load_config(requested), requested.parent, "file"

    example = Path.cwd() / "config.example.yaml"
    if example.is_file():
        return load_config(example), example.parent, "example"

    try:
        ref = resources.files("citedy_reddit_writer").joinpath("default_config.yaml")
        raw = yaml.safe_load(ref.read_text(encoding="utf-8"))
    except Exception:
        return None
    cfg = load_config_from_mapping(raw)
    return cfg, Path.cwd(), "bundled"


def _alert_webhook(url: str | None, message: str) -> None:
    if not url:
        return
    try:
        with httpx.Client() as client:
            client.post(
                url,
                json={"text": message, "source": "citedy-reddit-writer"},
                timeout=15.0,
            )
    except Exception as e:
        logging.getLogger(__name__).warning("Alert webhook failed: %s", e)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Reddit listings, filter, call Citedy POST /api/agent/autopilot.",
    )
    parser.add_argument(
        "--config",
        default=os.environ.get("CITEDY_REDDIT_CONFIG", "config.yaml"),
        help="Path to YAML config (or set CITEDY_REDDIT_CONFIG)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions only (no Citedy calls, no state updates)",
    )
    args = parser.parse_args(argv)

    resolved = _resolve_config_and_base(args.config)
    if resolved is None:
        print(
            f"Config not found: {Path(args.config).expanduser().resolve()}",
            file=sys.stderr,
        )
        print(
            "Put CITEDY_AGENT_API_KEY in .env, then either: create config.yaml, "
            "add config.example.yaml in the current directory, or upgrade citedy-reddit-writer "
            "(bundled defaults). Or run: citedy-reddit-setup",
            file=sys.stderr,
        )
        return 2

    cfg, config_base, config_source = resolved
    _setup_logging(cfg.logging.level)
    log = logging.getLogger(__name__)
    if config_source == "bundled":
        log.info(
            "No %s — using packaged default_config.yaml; add config.yaml to customize",
            args.config,
        )
    elif config_source == "example":
        log.info(
            "Using %s/config.example.yaml (create config.yaml to override)",
            config_base,
        )

    dry_run = args.dry_run or os.environ.get("DRY_RUN", "").lower() in (
        "1",
        "true",
        "yes",
    )
    alert_url = os.environ.get("CITEDY_ALERT_WEBHOOK_URL", "").strip() or None

    if not dry_run and not cfg.citedy.agent_api_key:
        log.error("Missing CITEDY_AGENT_API_KEY (or citedy.agent_api_key in config)")
        _alert_webhook(alert_url, "citedy-reddit-run: missing API key")
        return 2

    state_path = _resolve_path(config_base, cfg.dedupe.state_path)
    state: RunState = load_state(state_path)

    today_count = daily_count(state)
    if today_count >= cfg.run.max_articles_per_day:
        log.info(
            "Daily cap reached (%s >= %s), exiting",
            today_count,
            cfg.run.max_articles_per_day,
        )
        return 0

    remaining = cfg.run.max_articles_per_day - today_count
    n_jobs = min(cfg.run.articles_per_run, remaining)

    recent_titles: list[str] = []
    if cfg.dedupe.sync_recent_article_titles and not dry_run:
        try:
            with httpx.Client() as client:
                recent_titles = fetch_recent_article_titles(
                    client,
                    cfg,
                    cfg.dedupe.recent_articles_limit,
                )
            log.info("Loaded %d recent article titles from API", len(recent_titles))
        except Exception as e:
            log.warning("Could not sync recent articles: %s", e)

    posts = fetch_all_candidates(cfg)
    candidates = filter_candidates(cfg, posts, state, recent_titles)
    if not candidates:
        log.info("No candidates after filter/dedupe")
        return 0

    picked = candidates[:n_jobs]
    log.info("Starting %d autopilot job(s)", len(picked))

    exit_code = 0
    with httpx.Client() as client:
        for post in picked:
            topic = format_topic(cfg.run.topic_template, post)
            source_urls = [post.url]

            if dry_run:
                log.info("DRY_RUN: would call autopilot topic=%r url=%s", topic, post.url)
                continue

            try:
                status, payload = post_autopilot(client, cfg, topic, source_urls)
            except Exception as e:
                log.exception("autopilot request failed: %s", e)
                exit_code = 1
                _alert_webhook(alert_url, f"citedy-reddit-run: autopilot request error: {e}")
                break

            if status not in (200, 202):
                log.error("autopilot HTTP %s: %s", status, json.dumps(payload)[:500])
                exit_code = 1
                _alert_webhook(
                    alert_url,
                    f"citedy-reddit-run: autopilot HTTP {status}: {payload.get('message', payload)}",
                )
                break

            if status == 202:
                job_id = extract_job_id(payload)
                if not job_id:
                    log.error("202 but no job id: %s", payload)
                    exit_code = 1
                    _alert_webhook(alert_url, "citedy-reddit-run: 202 without job id")
                    break
                log.info("Queued job %s", job_id)
                try:
                    final = poll_article_job(client, cfg, job_id, cfg.poll)
                except Exception as e:
                    log.exception("poll failed: %s", e)
                    exit_code = 1
                    _alert_webhook(alert_url, f"citedy-reddit-run: poll failed: {e}")
                    break
                if not is_poll_success(final):
                    log.error("Job failed: %s", final)
                    exit_code = 1
                    _alert_webhook(alert_url, f"citedy-reddit-run: job failed: {final}")
                    break
                log.info(
                    "Job complete: article_id=%s status=%s",
                    final.get("article_id"),
                    final.get("status"),
                )
            else:
                st = str(payload.get("status") or "")
                if st == "failed" or payload.get("save_failed"):
                    log.error("Sync generation failed: %s", payload)
                    exit_code = 1
                    _alert_webhook(
                        alert_url,
                        f"citedy-reddit-run: sync failed: {payload.get('message', payload)}",
                    )
                    break
                aid = extract_sync_article_id(payload)
                log.info(
                    "Sync response: article_id=%s status=%s",
                    aid,
                    payload.get("status"),
                )

            state.post_ids.append(post.id)
            state.title_hashes.append(title_hash(post.title))
            increment_daily(state)
            trim_state(state, cfg.dedupe.max_tracked_post_ids)
            save_state(state_path, state)

    if dry_run:
        return 0
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
