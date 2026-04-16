# Deployment & publishing guide

This document explains **where the project lives**, **how it gets to GitHub and PyPI**, and **what to run** so nothing is lost across machines or months later.

## Source of truth (canonical tree)

| Location                                                                                                | Role                                                                 |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Monorepo path** `saas-blog/citedy-reddit-writer/`                                                     | Day-to-day edits, Cursor/IDE workspace, review in PRs.               |
| **Public Git** [github.com/citedy/citedy-reddit-writer](https://github.com/citedy/citedy-reddit-writer) | What users and CI clone; must stay in sync with the monorepo folder. |
| **PyPI** [pypi.org/project/citedy-reddit-writer](https://pypi.org/project/citedy-reddit-writer)         | Installable package; built from tags via GitHub Actions.             |

**Rule:** Edit code and docs under **`saas-blog/citedy-reddit-writer/`**, then **publish to the citedy repo** with the flow below. Do not treat the small GitHub repo as the only copy of development history—your full history stays in **`saas-blog`** (unless you switch to developing only in the citedy repo).

## What syncs to the public repo

`git subtree split --prefix=citedy-reddit-writer` copies **only** that directory’s tree into a branch whose root **is** the package (no `saas-blog/` prefix). That branch is pushed to **`citedy/citedy-reddit-writer`** `main`.

Included in the subtree:

- Python package `citedy_reddit_writer/`, `pyproject.toml`, `README.md`
- `.github/workflows/` (CI + PyPI publish)
- `packaging/github/` (workflow templates + `install-workflows.sh`)
- `scripts/push-to-citedy-remote.sh` (optional one-shot push from monorepo root)
- Skills under `.claude/`, `.cursor/`, etc.

**Not** included: anything outside `citedy-reddit-writer/` in the monorepo.

## One-time PyPI / GitHub setup (already done for this project)

1. **PyPI** — _Pending publisher_ / trusted publisher: project `citedy-reddit-writer`, repo `citedy/citedy-reddit-writer`, workflow `publish-pypi.yml`, environment `pypi`.
2. **GitHub** — repository **Environment** named **`pypi`** (Settings → Environments). Used by the publish workflow for OIDC.

If you recreate a repo or rename workflows, update the trusted publisher on PyPI to match.

## Day-to-day: push documentation or code to GitHub

From **`saas-blog`** root:

```bash
git add citedy-reddit-writer/
git commit -m "your message"
```

Publish to **citedy/citedy-reddit-writer**:

**Option A — helper script**

```bash
bash citedy-reddit-writer/scripts/push-to-citedy-remote.sh
```

**Option B — manual**

```bash
REMOTE=citedy-reddit-writer
BRANCH=citedy-reddit-writer-split
git remote get-url "$REMOTE" >/dev/null 2>&1 || \
  git remote add "$REMOTE" https://github.com/citedy/citedy-reddit-writer.git
git branch -D "$BRANCH" 2>/dev/null || true
git subtree split --prefix=citedy-reddit-writer -b "$BRANCH"
git push "$REMOTE" "$BRANCH:main"
```

`subtree split` on a large monorepo can take **minutes**; that is normal.

### Git remote name

The examples use remote name **`citedy-reddit-writer`**. If you use another name, substitute it in `git push` and tagging commands below.

## Release a new version to PyPI

1. Bump **`version`** in `citedy-reddit-writer/pyproject.toml` (must be **unique** on PyPI).
2. Commit in **`saas-blog`**, then run the **subtree push** (script or manual) so **`citedy/citedy-reddit-writer`** `main` contains the bump.
3. **Tag the commit that exists on the citedy repo**, not a random monorepo-only SHA:

   ```bash
   # If local split branch still exists:
   git tag v0.1.1 citedy-reddit-writer-split
   git push citedy-reddit-writer v0.1.1

   # If you deleted the split branch:
   git fetch citedy-reddit-writer main
   git tag v0.1.1 citedy-reddit-writer/main
   git push citedy-reddit-writer v0.1.1
   ```

4. GitHub Actions runs **Publish to PyPI** on tag `v*`. The PyPI project page description comes from **`README.md` at build time**—so README changes without a new release do **not** update PyPI until the next upload.

## CI on the public repo

- **`ci.yml`** — on push/PR to `main`: builds wheel/sdist and smoke-runs `citedy-reddit-run --help`.
- **`publish-pypi.yml`** — on push of tag `v*`: build + upload to PyPI via **trusted publishing** (no long-lived PyPI token in secrets).

## Workflow file sources

Canonical copies for editing live in **`packaging/github/`** (`publish-pypi.yml`, `ci.yml`). **`packaging/github/install-workflows.sh`** copies them into **`.github/workflows/`** if you need to regenerate. The **citedy** repo should always contain **`.github/workflows/`** as pushed from the monorepo subtree.

## Secrets and files to never commit

- **`.env`** (API keys)
- **`config.yaml`** with a real `agent_api_key`
- Local **`data/`** or state files if they contain sensitive paths

Use **`.env.example`** and **`config.example.yaml`** only for templates.

## Quick checklist (copy for a release)

- [ ] `pyproject.toml` version bumped
- [ ] Changes committed under `saas-blog`
- [ ] Subtree push to `citedy/citedy-reddit-writer` `main`
- [ ] Tag `vX.Y.Z` on **split remote** tip, `git push citedy-reddit-writer vX.Y.Z`
- [ ] Confirm Actions: CI green, Publish to PyPI green
- [ ] Verify: `pip index versions citedy-reddit-writer`

## Troubleshooting

| Symptom                            | What to check                                                                                                                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| PyPI publish fails (OIDC)          | PyPI trusted publisher matches **owner/repo/workflow/environment**; GitHub **Environment `pypi`** exists.                                                    |
| Tag push does not trigger publish  | Tag must point to a commit **present on** `citedy/citedy-reddit-writer`; use `citedy-reddit-writer-split` or `citedy-reddit-writer/main` as described above. |
| “Nothing new” on GitHub after push | Only **`citedy-reddit-writer/`** subtree updates the citedy repo; hard-refresh the README or open **Commits**.                                               |
| Subtree split very slow            | Large monorepo history; wait or run from a machine with SSD and full git object cache.                                                                       |
