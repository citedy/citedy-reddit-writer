#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "${ROOT}/.github/workflows"
cp "${ROOT}/packaging/github/publish-pypi.yml" "${ROOT}/.github/workflows/publish-pypi.yml"
cp "${ROOT}/packaging/github/ci.yml" "${ROOT}/.github/workflows/ci.yml"
echo "OK: ${ROOT}/.github/workflows/publish-pypi.yml"
echo "OK: ${ROOT}/.github/workflows/ci.yml"
