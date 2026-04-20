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
    while IFS= read -r line || [[ -n "$line" ]]; do
      local key=""
      local value=""

      line="${line%$'\r'}"
      [[ -z "${line//[[:space:]]/}" ]] && continue
      [[ "$line" =~ ^[[:space:]]*# ]] && continue

      line="${line#"${line%%[![:space:]]*}"}"
      if [[ "$line" == export[[:space:]]* ]]; then
        line="${line#export }"
        line="${line#"${line%%[![:space:]]*}"}"
      fi

      [[ "$line" == *=* ]] || continue

      key="${line%%=*}"
      value="${line#*=}"
      key="${key%"${key##*[![:space:]]}"}"

      [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

      if [[ ${#value} -ge 2 ]]; then
        if [[ "${value:0:1}" == '"' && "${value: -1}" == '"' ]]; then
          value="${value:1:${#value}-2}"
        elif [[ "${value:0:1}" == "'" && "${value: -1}" == "'" ]]; then
          value="${value:1:${#value}-2}"
        fi
      fi

      printf -v "$key" '%s' "$value"
      export "$key"
    done < "$f"
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
