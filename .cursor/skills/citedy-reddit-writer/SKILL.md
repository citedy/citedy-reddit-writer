---
name: citedy-reddit-writer
description: "Reddit listings → Citedy POST /api/agent/autopilot (no scout credits). citedy-reddit-run; setup optional if defaults OK. Use when user says citedy reddit writer, reddit autopilot cron, citedy-reddit-run, or OpenClaw Reddit articles."
---

# citedy-reddit-writer (Cursor)

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

Put **`CITEDY_AGENT_API_KEY`** in **`.env`**. You do **not** need `config.yaml` for the first run — the package includes **`default_config.yaml`** (bundled). Run:

```bash
set -a && source .env && set +a
citedy-reddit-run --dry-run
citedy-reddit-run
```

Use **`citedy-reddit-setup`** when the user wants custom subreddits, filters, or caps.

## In Cursor

1. Work from repo root (where `pyproject.toml` lives).
2. Install venv + `pip install -e .` if entrypoints missing.
3. If key is in `.env`, run **`npm run ...`** or **`citedy-reddit-run`** — do not require the wizard unless customizing.
4. Prefer **`--dry-run`** for safe tests.

**saas-blog monorepo:** from **monorepo root**: **`npm run citedy-reddit-writer -- --dry-run`** or **`npm run citedy-reddit-writer`** (loads `../.env` + `citedy-reddit-writer/.env`). Or **`bash citedy-reddit-writer/run-with-env.sh`**. Package dir: **`citedy-reddit-writer/`**. Skills at repo root: **`.cursor/...`**, **`.codex/...`**, **`.claude/...`**.

**Parity:** Keep this file in sync with **`.codex/skills/citedy-reddit-writer/SKILL.md`** and **`.claude/skills/citedy-reddit-writer/SKILL.md`** when editing OSS instructions.
