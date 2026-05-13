#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${AUDIO2TEXT_MODEL_REPO:-Rok2025/audio2text}"
TAG="${AUDIO2TEXT_MODEL_TAG:-models-v1}"
ASSET="${AUDIO2TEXT_MODEL_ASSET:-audio2text-models-v1.tar.gz}"
URL="${AUDIO2TEXT_MODEL_URL:-https://github.com/${REPO}/releases/download/${TAG}/${ASSET}}"
TMP_FILE="${TMPDIR:-/tmp}/${ASSET}"

cd "${ROOT_DIR}"

echo "Downloading models from ${URL}"
if command -v curl >/dev/null 2>&1; then
  curl -L --fail -o "${TMP_FILE}" "${URL}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${TMP_FILE}" "${URL}"
else
  echo "curl or wget is required to download models" >&2
  exit 1
fi

mkdir -p models
tar -xzf "${TMP_FILE}" -C "${ROOT_DIR}"

test -f models/paraformer-zh/model.pt
test -f models/fsmn-vad/model.pt

echo "Models are ready in ${ROOT_DIR}/models"
