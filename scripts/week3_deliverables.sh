#!/usr/bin/env bash
# Build Week 3 production bundle (POSIX). From repo root:
#   chmod +x scripts/week3_deliverables.sh
#   ./scripts/week3_deliverables.sh [path/to/atpg_file]

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/python"
OUT="${WEEK3_OUT:-deliverables}"
ATPG="${1:-}"

if [[ -n "$ATPG" ]]; then
  python "${ROOT}/python/integrated_flow/week3_production.py" --atpg "$ATPG" --out "$OUT"
else
  python "${ROOT}/python/integrated_flow/week3_production.py" --dry-run --out "$OUT"
fi

echo "Week 3 bundle written to ${OUT}/"
