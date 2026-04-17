---
name: citedy-reddit-writer
description: "One-shot Reddit→Citedy autopilot runner + interactive setup. Triggers: citedy reddit writer, reddit autopilot cron, /citedy-reddit-writer, citedy-reddit-run, citedy-reddit-setup."
---

# citedy-reddit-writer

OSS package: [github.com/citedy/citedy-reddit-writer](https://github.com/citedy/citedy-reddit-writer)

## What it does

1. Fetches **public** Reddit hot/new/top listings for configured subreddits.
2. Filters (keywords, score, age) and **dedupes** (local `data/state.json` + optional recent titles from `GET /api/agent/articles`).
3. Calls **`POST /api/agent/autopilot`** with `topic` + `source_urls: [thread URL]`, `auto_publish` as configured.
4. On **202**, polls **`GET /api/agent/articles/{jobId}`** until terminal status.

Does **not** use **`POST /api/agent/scout/reddit`** (saves scout credits).

## First-time install

From the **clone root** (directory containing `pyproject.toml`):

```bash
python3 -m venv .venv && source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
pip install -e .
```

## API key only (v0.1.1+)

If **`CITEDY_AGENT_API_KEY`** is in the environment (or **`.env`**), **`citedy-reddit-run`** uses **packaged defaults** when there is no `config.yaml`. No wizard required for a first run. Users who want custom subreddits/filters run **`citedy-reddit-setup`** once (writes **`config.yaml`** + **`.env`**). Never commit `.env`.

## Every run

```bash
cd /path/to/citedy-reddit-writer   # or monorepo: use npm script from root — see below
set -a && source .env && set +a
citedy-reddit-run --dry-run        # safe
citedy-reddit-run                  # uses config.yaml if present, else config.example.yaml, else bundled defaults
```

- **`--dry-run`** — Reddit + filters only; no Citedy, no state updates.
- No `config.yaml` → bundled **`default_config.yaml`** inside the package (see repo `citedy_reddit_writer/default_config.yaml`). Relative paths (e.g. state file) resolve from **current working directory**.

## Agent behavior when user says `/citedy-reddit-writer`

1. **Monorepo (saas-blog) — from workspace root:** **`npm run citedy-reddit-writer -- --dry-run`** / **`npm run citedy-reddit-writer`** (loads parent `.env` + `citedy-reddit-writer/.env`). Requires **`pip install -e .`** in `citedy-reddit-writer/` once.
2. If **`CITEDY_AGENT_API_KEY`** missing → ask user to add it to **`.env`** (or run **`citedy-reddit-setup`**). Do **not** block on questions if the key is already loadable from env.
3. Prefer **`--dry-run`** first when user is testing.
4. Optional **`citedy-reddit-setup`** only when they need non-default subreddits/limits.

## IDE MCP vs this tool

- **Citedy MCP** in Cursor/Claude: good for interactive agents.
- **This CLI**: good for **cron/systemd** — plain HTTPS, no MCP transport.

See also: `.claude/skills/mcp-reddit` (overview of MCP vs scheduled runs).
