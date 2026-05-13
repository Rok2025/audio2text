#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if command -v uv >/dev/null 2>&1; then
  uv python install 3.11
  uv venv .venv --python 3.11
  uv pip install --python .venv/bin/python -r requirements.txt
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
  "$PYTHON_BIN" -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

.venv/bin/python scripts/check_env.py
