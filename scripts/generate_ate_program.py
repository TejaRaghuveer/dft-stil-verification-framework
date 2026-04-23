#!/usr/bin/env python3
"""ATE Test Program Generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from post_silicon.ate_validation import ATEProgramBuilder, STILPatternParser


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ATE test program")
    parser.add_argument("--stil_file", required=True, help="Input STIL file")
    parser.add_argument("--ate_type", required=True, help="Tester type (V93000, LTX_CREDENCE, XCERRA)")
    parser.add_argument("--output", required=True, help="Output program file")
    args = parser.parse_args()

    stil = STILPatternParser(args.stil_file)
    patterns = stil.get_all_patterns()

    ate_builder = ATEProgramBuilder(ate_type=args.ate_type)
    for pattern in patterns:
        ate_builder.add_pattern(pattern)

    ate_builder.add_procedure("initialization", "INIT_DUT")
    ate_builder.add_procedure("test_execution", "RUN_ALL_PATTERNS")
    ate_builder.add_procedure("shutdown", "SHUTDOWN")
    ate_builder.generate_program(output_file=args.output)
    print(f"ATE program generated: {args.output}")


if __name__ == "__main__":
    main()

