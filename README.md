# citedy-reddit-writer

Public Reddit listings (`.json` API) → filter/dedupe → **Citedy** [`POST /api/agent/autopilot`](https://www.citedy.com) with `source_urls` and optional **`auto_publish`**. Does **not** call `scout/reddit` (no scout credits per tick).

**Repository:** [github.com/citedy/citedy-reddit-writer](https://github.com/citedy/citedy-reddit-writer)

## Quick start

```bash
git clone https://github.com/citedy/citedy-reddit-writer.git
cd citedy-reddit-writer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Interactive: creates config.yaml + .env (API key only in .env)
citedy-reddit-setup

set -a && source .env && set +a
citedy-reddit-run --config config.yaml
```

Dry-run (no Citedy calls, no state writes):

```bash
citedy-reddit-run --config config.yaml --dry-run
```

## Agent skills (Claude Code, Cursor, Codex)

| Environment     | Skill / command location                                                                                                                  |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Claude Code** | `.claude/skills/citedy-reddit-writer/SKILL.md` + **`/citedy-reddit-writer`** (`.claude/commands/citedy-reddit-writer.md`)                 |
| **Cursor**      | In **saas-blog** monorepo: `.cursor/skills/citedy-reddit-writer/SKILL.md` (triggers on “citedy reddit writer”, `citedy-reddit-run`, etc.) |
| **Codex**       | In **saas-blog** monorepo: `.codex/skills/citedy-reddit-writer/SKILL.md`                                                                  |

**Standalone clone** ships **`.claude/`** and **`.cursor/skills/citedy-reddit-writer/`**. For **Codex** only, copy **`.codex/skills/citedy-reddit-writer/SKILL.md`** from the saas-blog monorepo if needed.

**Verify in Cursor:** open this workspace, start a chat, ask e.g. “Run citedy-reddit-writer dry-run from `citedy-reddit-writer`” — the agent should load the skill and `cd citedy-reddit-writer` then run `./.venv/bin/citedy-reddit-run --config config.example.yaml --dry-run` (after `pip install -e .` if needed).

## Requirements

- Python 3.10+
- `CITEDY_AGENT_API_KEY` (Bearer `citedy_agent_…`)
- [Reddit API / data terms](https://www.redditinc.com/policies/data-api-terms) — sensible `User-Agent`, no abusive polling

## Configuration

- **`citedy-reddit-setup`** — prompts for base URL, key, subreddits, filters, caps, `auto_publish`, writes `config.yaml` + `.env`.
- **`config.example.yaml`** — full YAML reference if you edit by hand.
- Env: `CITEDY_AGENT_API_KEY`, `CITEDY_REDDIT_CONFIG`, optional `CITEDY_BASE_URL`, `CITEDY_ALERT_WEBHOOK_URL`, `DRY_RUN`.

State file path (`dedupe.state_path`) is resolved relative to the config file directory.

## Scheduling

- **systemd:** `systemd/citedy-reddit-writer.service` + `citedy-reddit-writer.timer`
- **cron:** `crontab.example`

## Security

Do not commit `.env` or a `config.yaml` that contains `agent_api_key`. Prefer an empty key in YAML and load from the environment.

## License

MIT — see `LICENSE`.
