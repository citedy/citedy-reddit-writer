---
name: citedy-reddit-writer
description: "Run or set up citedy-reddit-writer (Reddit→autopilot). Use when user says /citedy-reddit-writer, reddit writer, reddit autopilot cron."
---

# /citedy-reddit-writer

Follow the **citedy-reddit-writer** skill in this repo: `.claude/skills/citedy-reddit-writer/SKILL.md`.

**Monorepo:** package lives at `citedy-reddit-writer/` (repo root). `cd` there, `pip install -e .`, then:

- First time: `citedy-reddit-setup`
- Run: `set -a && source .env && set +a && citedy-reddit-run --config config.yaml`
- Safe test: add `--dry-run`

Do not paste or commit `CITEDY_AGENT_API_KEY`; it belongs in `.env` only.
