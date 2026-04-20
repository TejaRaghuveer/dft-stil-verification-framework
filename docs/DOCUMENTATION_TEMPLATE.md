# Documentation Template Library

Use this template for consistent class-level documentation.

## Class: dft_scoreboard

### Purpose

Verifies DFT test patterns by comparing expected vs. actual responses.

### Configuration Parameters

- `comparison_mode`: EXACT_MATCH or TIMING_MARGIN (default: EXACT_MATCH)
- `failure_log_file`: Path to save failures (default: "failures.log")
- `stop_on_first_failure`: Boolean (default: false)

### Methods

- `add_expected_response(pattern_name, expected_vector)`
- `add_actual_response(pattern_name, actual_vector)`
- `compare_all()`: Perform all comparisons and report results

### Example Usage

```systemverilog
dft_scoreboard scoreboard = new("scoreboard");
scoreboard.set_comparison_mode(EXACT_MATCH);
scoreboard.add_expected_response("PATTERN_001", 32'hABCD1234);
scoreboard.add_actual_response("PATTERN_001", 32'hABCD1234);
scoreboard.compare_all();  // Returns: PASS
```

### See Also

- [Fault Coverage Analysis](../docs/deep_dives/fault_coverage.md)
- [Pattern Verification](../docs/USER_GUIDE.md)

