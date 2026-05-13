#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -x ".venv/bin/python" ]; then
  echo "Missing .venv/bin/python. Run: bash scripts/setup_env.sh" >&2
  exit 1
fi

exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
