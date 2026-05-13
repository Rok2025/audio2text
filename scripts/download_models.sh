#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${AUDIO2TEXT_MODEL_REPO:-Rok2025/audio2text}"
TAG="${AUDIO2TEXT_MODEL_TAG:-models-v1}"
ASSET="${AUDIO2TEXT_MODEL_ASSET:-audio2text-models-v1.tar.gz}"
URL="${AUDIO2TEXT_MODEL_URL:-https://github.com/${REPO}/releases/download/${TAG}/${ASSET}}"
CHECKSUM_URL="${AUDIO2TEXT_MODEL_CHECKSUM_URL:-${URL}.sha256}"
TMP_FILE="${TMPDIR:-/tmp}/${ASSET}"
CHECKSUM_FILE="${TMP_FILE}.sha256"

cd "${ROOT_DIR}"

echo "Downloading models from ${URL}"
if command -v curl >/dev/null 2>&1; then
  curl -L --fail -o "${TMP_FILE}" "${URL}"
  if curl -L --fail -o "${CHECKSUM_FILE}" "${CHECKSUM_URL}"; then
    HAS_CHECKSUM=1
  else
    HAS_CHECKSUM=0
  fi
elif command -v wget >/dev/null 2>&1; then
  wget -O "${TMP_FILE}" "${URL}"
  if wget -O "${CHECKSUM_FILE}" "${CHECKSUM_URL}"; then
    HAS_CHECKSUM=1
  else
    HAS_CHECKSUM=0
  fi
else
  echo "curl or wget is required to download models" >&2
  exit 1
fi

if [ "${HAS_CHECKSUM}" = "1" ]; then
  echo "Verifying checksum"
  if command -v sha256sum >/dev/null 2>&1; then
    (cd "$(dirname "${TMP_FILE}")" && sha256sum -c "$(basename "${CHECKSUM_FILE}")")
  elif command -v shasum >/dev/null 2>&1; then
    (cd "$(dirname "${TMP_FILE}")" && shasum -a 256 -c "$(basename "${CHECKSUM_FILE}")")
  else
    echo "sha256sum or shasum is not available; skip checksum verification"
  fi
else
  echo "Checksum file not found; skip checksum verification"
fi

mkdir -p models
tar -xzf "${TMP_FILE}" -C "${ROOT_DIR}"

test -f models/paraformer-zh/model.pt
test -f models/fsmn-vad/model.pt

echo "Models are ready in ${ROOT_DIR}/models"
