#!/usr/bin/env bash
# Run from saas-blog monorepo root:
#   bash citedy-reddit-writer/scripts/push-to-citedy-remote.sh
#
# 1) Creates GitHub Environment "pypi" (for Trusted Publishing).
# 2) Commits citedy-reddit-writer/ on current branch (if dirty).
# 3) git subtree split → pushes to citedy/citedy-reddit-writer main.

set -euo pipefail

MONO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_NAME="citedy-reddit-writer"
REMOTE_URL="https://github.com/citedy/citedy-reddit-writer.git"
SPLIT_BRANCH="citedy-reddit-writer-split"

cd "$MONO_ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not found"
  exit 1
fi

echo "==> Ensure GitHub Environment: pypi"
if ! echo '{}' | gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/citedy/citedy-reddit-writer/environments/pypi" \
  --input - 2>/dev/null; then
  echo "    warning: could not create env via API — add Environment 'pypi' in repo Settings → Environments"
fi

echo "==> Stage and commit citedy-reddit-writer (if needed)"
git add citedy-reddit-writer
if git diff --staged --quiet; then
  echo "    nothing to commit (already clean)"
else
  git commit -m "chore(citedy-reddit-writer): package + PyPI GitHub Actions"
fi

if ! git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git remote add "$REMOTE_NAME" "$REMOTE_URL"
fi

echo "==> subtree split → $SPLIT_BRANCH"
git branch -D "$SPLIT_BRANCH" 2>/dev/null || true
git subtree split --prefix=citedy-reddit-writer -b "$SPLIT_BRANCH"

echo "==> push to $REMOTE_URL (main)"
git push -u "$REMOTE_NAME" "$SPLIT_BRANCH:main"

echo "==> done. Next: open Actions on GitHub (CI), then tag the SPLIT tip (not monorepo HEAD):"
echo "    git tag v0.1.0 $SPLIT_BRANCH && git push $REMOTE_NAME v0.1.0"
echo "    (or after fetch: git fetch $REMOTE_NAME main && git tag v0.1.0 $REMOTE_NAME/main && git push $REMOTE_NAME v0.1.0)"
