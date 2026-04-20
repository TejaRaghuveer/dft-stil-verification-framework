#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[setup] Repository root: ${ROOT_DIR}"
echo "[setup] Python: $(python --version 2>/dev/null || python3 --version)"

if [[ -f "scripts/setup_env.sh" ]]; then
  # shellcheck source=/dev/null
  source "scripts/setup_env.sh" || true
fi

mkdir -p reports logs .cache performance patterns/signoff

if [[ -f "requirements.txt" ]]; then
  python -m pip install --upgrade pip >/dev/null
  pip install -r requirements.txt >/dev/null
fi

echo "[setup] Environment setup complete"
