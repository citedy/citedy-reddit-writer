# citedy-reddit-writer (Codex)

Repo: [github.com/citedy/citedy-reddit-writer](https://github.com/citedy/citedy-reddit-writer)

**Workspace root** for this clone is the directory that contains **`pyproject.toml`** (not a subfolder). All commands run from **`.`** (repo root).

## What it does

1. Public Reddit listings → filter/dedupe → **`POST /api/agent/autopilot`** with `source_urls`.
2. Poll **`GET /api/agent/articles/{jobId}`** on **202**.
3. Does **not** use **`scout/reddit`**.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## API key only (v0.1.1+)

Put **`CITEDY_AGENT_API_KEY`** in **`.env`**. No **`config.yaml`** required for first run — packaged **`default_config.yaml`** is used when no local config exists.

```bash
set -a && source .env && set +a
citedy-reddit-run --dry-run
citedy-reddit-run
```

**`citedy-reddit-setup`** — optional, for custom subreddits/filters.

## Run

```bash
set -a && source .env && set +a
citedy-reddit-run --dry-run
citedy-reddit-run
```

**Dry-run:** safe test (no Citedy calls, no state updates).

## In Cursor / Codex

1. Work from repo root (where `pyproject.toml` lives).
2. Install venv + `pip install -e .` if entrypoints missing.
3. With key in `.env`, run the CLI — avoid unnecessary questions; wizard only for customization.
4. Prefer **`--dry-run`** for safe tests.

**saas-blog monorepo:** from **monorepo root**: **`npm run citedy-reddit-writer -- --dry-run`** or **`npm run citedy-reddit-writer`** (uses **`run-with-env.sh`**: parent `.env` + `citedy-reddit-writer/.env`). Same paths: **`.cursor/...`**, **`.codex/...`**, **`.claude/...`**, slash **`/citedy-reddit-writer`**.

**Parity:** Keep this file in sync with **`.cursor/skills/citedy-reddit-writer/SKILL.md`** in this package when editing OSS instructions.
