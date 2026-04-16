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

## First-time setup (human or agent)

From the **clone root** (directory containing `pyproject.toml`):

```bash
python3 -m venv .venv && source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
pip install -e .
citedy-reddit-setup
```

`citedy-reddit-setup` writes **`config.yaml`** and **`.env`** (`CITEDY_AGENT_API_KEY` + `CITEDY_REDDIT_CONFIG`). Never commit `.env`.

Re-run with **`--force`** only to overwrite existing files.

## Every run

```bash
cd /path/to/citedy-reddit-writer
set -a && source .env && set +a
citedy-reddit-run --config config.yaml
```

- **`--dry-run`** — Reddit + filters only; no Citedy, no state updates.
- Missing config → tell user to run **`citedy-reddit-setup`** first.

## Agent behavior when user says `/citedy-reddit-writer`

1. **`cd`** to this repo’s root (directory with `pyproject.toml`). In the **saas-blog** monorepo that is **`citedy-reddit-writer/`** under the workspace root.
2. If **`config.yaml`** or **`.env`** missing → run **`citedy-reddit-setup`** (user completes prompts in terminal; key is hidden input).
3. If user wants a test without spend → **`citedy-reddit-run --config config.yaml --dry-run`**.
4. Otherwise → **`citedy-reddit-run --config config.yaml`** (may charge autopilot credits and publish).

## IDE MCP vs this tool

- **Citedy MCP** in Cursor/Claude: good for interactive agents.
- **This CLI**: good for **cron/systemd** — plain HTTPS, no MCP transport.

See also: `.claude/skills/mcp-reddit` (overview of MCP vs scheduled runs).
