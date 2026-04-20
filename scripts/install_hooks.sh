#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git -C "${ROOT_DIR}" config core.hooksPath .githooks
chmod +x "${ROOT_DIR}/.githooks/pre-commit"
echo "Installed git hooks from .githooks/"

if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install
  echo "Installed pre-commit framework hooks."
else
  echo "pre-commit not found. Install with: pip install pre-commit"
fi
