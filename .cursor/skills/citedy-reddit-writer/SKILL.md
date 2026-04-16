---
name: citedy-reddit-writer
description: "Reddit listings → Citedy POST /api/agent/autopilot (no scout credits). citedy-reddit-setup + citedy-reddit-run. Use when user says citedy reddit writer, reddit autopilot cron, citedy-reddit-run, or OpenClaw Reddit articles."
---

# citedy-reddit-writer (Cursor)

Repo: [github.com/citedy/citedy-reddit-writer](https://github.com/citedy/citedy-reddit-writer)

**Workspace root** for this clone is the directory that contains **`pyproject.toml`** (not a subfolder). All commands run from **`.`** (repo root).

## What it does

1. Public Reddit listings → filter/dedupe → **`POST /api/agent/autopilot`** with `source_urls`.
2. Poll **`GET /api/agent/articles/{jobId}`** on **202**.
3. Does **not** use **`scout/reddit`**.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
citedy-reddit-setup
```

## Run

```bash
set -a && source .env && set +a
citedy-reddit-run --config config.yaml
```

**Dry-run:** `citedy-reddit-run --config config.example.yaml --dry-run`

## In Cursor

1. Work from repo root (where `pyproject.toml` lives).
2. Install venv + `pip install -e .` if entrypoints missing.
3. Use **`citedy-reddit-setup`** until `config.yaml` and `.env` exist.
4. Prefer **`--dry-run`** for safe tests.

**saas-blog monorepo:** package lives at **`citedy-reddit-writer/`** under the Next.js repo root; use **`cd citedy-reddit-writer`** there. Skill copy: **`.cursor/skills/citedy-reddit-writer/SKILL.md`** at monorepo root.
