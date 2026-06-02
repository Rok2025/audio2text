#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if docker compose version >/dev/null 2>&1; then
  exec docker compose -f docker-compose.cn.yml up -d --build
fi

if command -v docker-compose >/dev/null 2>&1; then
  exec docker-compose -f docker-compose.cn.yml up -d --build
fi

echo "Missing Docker Compose. Install Docker Compose v2 or docker-compose." >&2
exit 1
