#!/bin/bash

# Pattern Debug Script

set -e

PATTERN_NAME=$1
ATPG_FILE=$2
DUT_MODEL=$3

if [ -z "$PATTERN_NAME" ] || [ -z "$ATPG_FILE" ]; then
  echo "Usage: $0 <PATTERN_NAME> <ATPG_FILE> [DUT_MODEL]"
  exit 1
fi

SIM_CMD=${SIM_CMD:-"./scripts/run_simulation.sh"}
SIMULATOR=${SIMULATOR:-"vcs"}
WAVE_EXT=${WAVE_EXT:-"vcd"}
TEST_NAME=${TEST_NAME:-"atpg_select_patterns_test"}

# 1. Extract specific pattern from ATPG file
python3 scripts/extract_pattern.py "$PATTERN_NAME" "$ATPG_FILE" > "pattern_${PATTERN_NAME}.txt"

# 2. Run testbench with single pattern
# If your simulator wrapper differs, override SIM_CMD env var.
$SIM_CMD -s "$SIMULATOR" -t "$TEST_NAME"

# Placeholders for dumped artifacts if sim infrastructure does not generate them automatically
[ -f "response_${PATTERN_NAME}.txt" ] || echo "" > "response_${PATTERN_NAME}.txt"
[ -f "pattern_${PATTERN_NAME}.${WAVE_EXT}" ] || echo "" > "pattern_${PATTERN_NAME}.${WAVE_EXT}"

# 3. Compare responses
python3 scripts/compare_responses.py \
  -pattern "pattern_${PATTERN_NAME}.txt" \
  -expected "pattern_${PATTERN_NAME}.expected" \
  -actual "response_${PATTERN_NAME}.txt" \
  -output "debug_report_${PATTERN_NAME}.html"

# 4. Generate waveform analysis
python3 scripts/analyze_waveform.py \
  -waveform "pattern_${PATTERN_NAME}.${WAVE_EXT}" \
  -output "waveform_report_${PATTERN_NAME}.html" \
  -highlight_failure

# 5. Suggest modifications
python3 scripts/suggest_fixes.py \
  -pattern "pattern_${PATTERN_NAME}.txt" \
  -failure "response_${PATTERN_NAME}.txt" \
  -output "fixes_${PATTERN_NAME}.txt"

echo "Debug complete. Results:"
echo "  Pattern: pattern_${PATTERN_NAME}.txt"
echo "  Waveform: pattern_${PATTERN_NAME}.${WAVE_EXT}"
echo "  Debug Report: debug_report_${PATTERN_NAME}.html"
echo "  Waveform Report: waveform_report_${PATTERN_NAME}.html"
echo "  Suggested Fixes: fixes_${PATTERN_NAME}.txt"
