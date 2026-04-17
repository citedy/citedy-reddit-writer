#!/usr/bin/env bash
# Run citedy-reddit-run with env from:
#   1) parent directory .env (e.g. saas-blog/.env in monorepo)
#   2) this package .env (overrides)
# Usage (from monorepo root):
#   bash citedy-reddit-writer/run-with-env.sh
#   bash citedy-reddit-writer/run-with-env.sh --dry-run
#   npm run citedy-reddit-writer -- --dry-run
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_ROOT="$SCRIPT_DIR"
PARENT_DIR="$(cd "$PKG_ROOT/.." && pwd)"

_load_env() {
  local f="$1"
  if [[ -f "$f" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$f"
    set +a
  fi
}

_load_env "$PARENT_DIR/.env"
_load_env "$PKG_ROOT/.env"

cd "$PKG_ROOT"

if [[ -x "$PKG_ROOT/.venv/bin/citedy-reddit-run" ]]; then
  exec "$PKG_ROOT/.venv/bin/citedy-reddit-run" "$@"
fi

if command -v citedy-reddit-run >/dev/null 2>&1; then
  exec citedy-reddit-run "$@"
fi

echo "citedy-reddit-run not found. Install: cd citedy-reddit-writer && python3 -m venv .venv && .venv/bin/pip install -e ." >&2
exit 1
