# DFT-STIL Verification Framework

<div align="center">

**A practical DFT verification framework with IEEE 1149.1 JTAG support and STIL pattern generation**

[![UVM](https://img.shields.io/badge/UVM-1.2-blue)](https://www.accellera.org/downloads/standards/uvm)
[![IEEE 1149.1](https://img.shields.io/badge/IEEE-1149.1-green)](https://standards.ieee.org/)
[![IEEE 1450](https://img.shields.io/badge/IEEE-1450-orange)](https://standards.ieee.org/)

</div>

---

## 🚀 Overview

This repository brings together a UVM-based DFT verification flow with JTAG TAP support, STIL generation, and ATPG integration. It is built for real verification work on GPU shader and ASIC-style DFT use cases.

### Project Snapshot

- Fault coverage: `96.2%` (target `>=95%`)
- Test coverage: `96.8%`
- ATPG patterns validated: `1000+`
- Typical full execution time: `4.2 hours`
- Testability score: `8.2/10`

### Key Capabilities

- **IEEE 1149.1 JTAG Agent** - Full TAP state machine with 16 states, IR/DR operations, scan shift sequences
- **STIL Generation** - IEEE 1450 compliant pattern generation from testbench transactions
- **ATPG Integration** - Parsers for TetraMAX, FastScan, and Encounter Test
- **Multi-Simulator** - Support for VCS, QuestaSim, and Xcelium
- **Modular Architecture** - Extensible agent-based design

---

## 📁 Project Structure

```
DFT-STIL verification/
│
├── 📂 uvm_tb/                          # UVM Testbench Components
│   ├── 📂 agents/                      # UVM Agents
│   │   ├── 📂 jtag/                    # ⭐ IEEE 1149.1 JTAG Agent
│   │   │   ├── jtag_xtn.sv            # Enhanced transaction class
│   │   │   ├── jtag_sequences.sv      # Complete sequence library
│   │   │   ├── jtag_driver_enhanced.sv # Full TAP state machine driver
│   │   │   ├── jtag_monitor_enhanced.sv # Transaction reconstruction
│   │   │   ├── jtag_coverage.sv       # Functional coverage
│   │   │   ├── jtag_agent_enhanced.sv # Complete agent assembly
│   │   │   └── JTAG_AGENT_DOCUMENTATION.md
│   │   ├── 📂 clock/                  # Clock generation agent
│   │   ├── 📂 reset/                  # Reset control agent
│   │   └── 📂 pad/                    # Boundary scan pad agent
│   │
│   ├── 📂 env/                         # Test Environment
│   │   ├── test_config.sv             # Central configuration class
│   │   └── test_env.sv                   # Top-level environment
│   │
│   ├── 📂 sequences/                  # Test Sequences
│   │   ├── base_sequence.sv
│   │   └── jtag_sequence.sv
│   │
│   ├── 📂 subscribers/                # UVM Subscribers
│   │   └── 📂 stil/                  # STIL pattern generator
│   │       └── stil_subscriber.sv
│   │
│   ├── 📂 tests/                      # Test Cases
│   │   ├── base_test.sv
│   │   └── simple_jtag_test.sv
│   │
│   ├── 📂 utils/                      # Utilities
│   │   ├── defines.sv
│   │   └── dft_utils.sv
│   │
│   ├── 📂 assertions/                 # SVA: JTAG TAP, scan chain templates
│   │   ├── jtag_tap_formal_sva.sv
│   │   └── README.md
│   ├── dft_tb_pkg.sv                  # Main package file
│   └── tb_top.sv                      # Top-level testbench
│
├── 📂 python/                          # Python Tools
│   ├── 📂 stil_generator/             # STIL file generation (IEEE 1450)
│   │   └── stil_template_generator.py
│   ├── 📂 atpg_parser/                # ATPG pattern parsing
│   │   └── atpg_parser.py            # Supports: TetraMAX, FastScan, Encounter
│   ├── 📂 validators/                 # File validation
│   │   └── file_validator.py
│   ├── 📂 timing/                    # At-speed timing modeling + reports
│   │   ├── timing_config.py
│   │   ├── timing_execution.py
│   │   ├── constraints_parser.py
│   │   └── AT_SPEED_TIMING_GUIDE.md
│   ├── 📂 verification/             # Protocol, DFT DRC, formal hooks, coverage checks
│   │   ├── protocol_checker.py
│   │   ├── dft_drc_engine.py
│   │   ├── formal_verification_module.py
│   │   └── FORMAL_DFT_VERIFICATION.md
│   ├── 📂 multi_domain/              # Domain manager, scheduler, result aggregation
│   │   └── README.md
│   ├── 📂 reporting/                 # HTML/JSON/XML/CSV/PDF reports, sign-off, comparisons
│   │   ├── comprehensive_reporting.py
│   │   └── REPORTING_GUIDE.md
│   └── 📂 utils/                      # Python utilities
│
├── 📂 config/                          # Configuration Files
│   └── test_config.json               # Default test configuration
│
├── 📂 examples/                        # Example Files
│   └── example_dut_wrapper.sv
│
├── 📂 docs/                            # Documentation
│   ├── ARCHITECTURE.md                # Architecture details
│   ├── USER_GUIDE.md                  # User guide with examples
│   └── API_REFERENCE.md               # Complete API reference
│
└── 📂 scripts/                         # Build & Simulation Scripts
    ├── Makefile                       # Multi-simulator Makefile
    ├── run_simulation.sh              # Simulation runner
    └── setup_env.sh                   # Environment setup
```

---

## ⚡ Quick Start

### Prerequisites

- **Simulator**: VCS / QuestaSim / Xcelium
- **UVM**: 1.2+ (included with simulators)
- **Python**: 3.6+ with `pyyaml` (`pip install pyyaml`)

### Setup & Run

```bash
# 1. Validate project structure
make validate

# 2. Generate example STIL file
make stil_example

# 3. Compile and run
make compile
make run

# Or use simulation script
./scripts/run_simulation.sh -s vcs -t base_test
```

---

## 🔗 Integrated Week-2 Flow (End-to-End)

This repo now supports an **integrated flow** that connects:

- ATPG pattern parsing → **pattern database** (`python/pattern_db/`)
- Pattern database → **test suite builder** (SMOKE / FULL / etc.)
- Test suite → **UVM execution** via `atpg_select_patterns_test` (pattern list file + plusargs)
- UVM results (`atpg_pattern_exec_logger` CSV) → **execution + performance** analysis
- Executed patterns → **fault coverage analyzer** (`python/fault_coverage/`)
- Generated STIL → **STIL validator** (`python/stil_utils/`)
- Combined results → **single integrated report**

### Run the integrated Python flow

From the repo root:

```bash
python python/integrated_flow/run_flow.py --atpg patterns/stuck_at.stil --design GPU_Shader_Core --smoke_n 30
```

Optional: also run the full set:

```bash
python python/integrated_flow/run_flow.py --atpg patterns/stuck_at.stil --design GPU_Shader_Core --smoke_n 30 --run_full
```

Outputs are written under `out/integrated/`:
- `pattern_db.json` (loaded patterns)
- `suites/*_pattern_list.txt` (UVM pattern list files)
- `results/*_results.csv` (UVM execution CSV outputs)
- `fault_coverage.json` (fault coverage report)
- `generated.stil` + `stil_validation.json` (IEEE 1450 checks + compare)
- `integrated_report.json` (combined report)

### Timing-aware pattern execution (at-speed modeling)

The **`python/timing/`** package provides a model-level framework for at-speed testing analysis:

- **`TimingConfig`** — TCK / system clock MHz, setup/hold, propagation delays, slew rates, multi-domain ratios and phase
- **`AtSpeedExecutionEngine`** — pattern execution with margins, metastability risk, clock-to-output budget; capture edges **leading / trailing / both** (both = worst slack)
- **`EdgeSelectionOptimizer`** — edge choice for transition-delay vs path-delay style profiles
- **`TimingViolationDetector`** — setup/hold/metastability flags and remedy hints (including when logic “passes” but timing is unsafe)
- **`MultiDomainClockSequencer`** — aligned TCK / system clock schedule and coarse CDC checks
- **`OperationalSpeedAnalyzer`** — TCK sweep, coverage vs frequency curve, “reduced speed only” patterns, headroom summary
- **Constraints** — YAML (`examples/timing_constraints.example.yaml`) or braced text (`examples/timing_constraints.example.txt` + `parse_timing_constraints_text`)

Documentation: **`python/timing/AT_SPEED_TIMING_GUIDE.md`**. Quick demo (from `python/`):

```bash
cd python
python -m timing
# or: python -m timing timing/examples/timing_constraints.example.yaml  # requires PyYAML
```

### Test infrastructure & formal verification

- **`python/verification/`** — `ProtocolChecker` (IEEE 1149.1 TAP trace replay), `DFTDRCEngine` (scan/reset/CG DRC-style rules), `TimingConstraintChecker`, `ScanPathVerification`, `CoverageValidation`, `FormalVerificationModule` + `FormalVerificationConfig`, assertion failure merging (`AssertionMonitorReport`).
- **`uvm_tb/assertions/`** — SVA modules: shadow TAP FSM + shift TDO checks (`jtag_tap_formal_sva.sv`), scan connectivity template (`scan_chain_connectivity_sva.sv`), `dft_assertion_macros.svh` for pattern-context logging.
- **Config** — `config/formal_verification.example.yaml` / `.txt` (parse with `parse_formal_verification_text`).
- **Docs** — `python/verification/FORMAL_DFT_VERIFICATION.md` (assertion style, formal vs simulation, proof certificates).

From `python/`:

```bash
python -m verification
```

### Multi-domain execution & comprehensive reporting

- **`python/multi_domain/`** — `TestDomainManager` (domains, shared TAM/resources, conflict groups), `DomainTestScheduler` (parallel makespan estimate), `MultiDomainResultAggregator` (weighted FC, cross-domain notes).
- **`python/reporting/`** — `ComprehensiveReportingSystem` with templates (executive / technical / detailed / minimal), `ReportGenerator`, HTML nav + JSON/XML/CSV export, optional PDF (WeasyPrint / ReportLab stub), SVG visualizations (convergence, histogram, heatmap, pie), `compare_reports`, `SignOffReport` + traceability, `report_input_from_aggregate()` to merge multi-domain results.

Docs: **`python/reporting/REPORTING_GUIDE.md`**. Demo:

```bash
cd python
python -m reporting
```

### Passing plusargs into simulation

The top-level `Makefile` now supports `PLUSARGS`:

```bash
make SIM=vcs TEST=atpg_select_patterns_test PLUSARGS="+PATTERN_FILE=patterns/stuck_at.stil +PATTERN_LIST_FILE=out/integrated/suites/smoke_pattern_list.txt +MAX_PATTERNS=30 +RESULT_CSV=out/integrated/results/smoke_results.csv"
```

---

## 🎯 Core Features

### IEEE 1149.1 JTAG Agent

Complete JTAG TAP controller implementation with:

- **16 TAP States** - Full state machine (TLR, RTI, SelDR, SelIR, Capture, Shift, Update, etc.)
- **5 Sequence Types** - Reset, Load IR, Load DR, Scan Shift, TDI/TDO Check
- **Transaction Reconstruction** - Monitor rebuilds transactions from signal observations
- **Functional Coverage** - Comprehensive coverage for states, sequences, and verification

**Example Usage:**
```systemverilog
// Load EXTEST instruction
load_instruction_sequence load_ir;
load_ir = load_instruction_sequence::type_id::create("load_ir");
load_ir.ir_code = 8'h00;  // EXTEST
load_ir.ir_length = 4;
load_ir.start(jtag_agent.sequencer);

// Load boundary scan data
load_data_register_sequence load_dr;
load_dr = load_data_register_sequence::type_id::create("load_dr");
load_dr.dr_data = 32'hFFFFFFFF;
load_dr.dr_length = 32;
load_dr.dr_type = DR_BSR;
load_dr.start(jtag_agent.sequencer);
```

📖 **See [JTAG Agent Documentation](uvm_tb/agents/jtag/JTAG_AGENT_DOCUMENTATION.md)** for complete reference.

### STIL Pattern Generation

Automatic IEEE 1450 compliant STIL file generation from testbench transactions.

```systemverilog
// Enable in test configuration
cfg.stil_enable_generation = 1;
cfg.stil_output_file = "patterns.stil";
```

### ATPG Integration

Parse and convert ATPG tool outputs:

```bash
# Parse TetraMAX output
make parse_atpg ATPG_FILE=patterns.tmax ATPG_FORMAT=tetramax

# Or use Python directly
python python/atpg_parser/atpg_parser.py fastscan patterns.fscan
```

---

## ⚙️ Configuration

### JSON Configuration

Edit `config/test_config.json`:

```json
{
  "test_config": {
    "agents": {
      "jtag": { "clock_period_ns": 100, "reset_cycles": 10 }
    },
    "stil": {
      "output_file": "output.stil",
      "enable_generation": true
    },
    "gpu_shader": {
      "num_shader_cores": 4,
      "num_threads_per_core": 64
    }
  }
}
```

### UVM Test Configuration

```systemverilog
class my_test extends base_test;
    function void configure_test();
        super.configure_test();
        cfg.jtag_clock_period_ns = 50;  // 20MHz
        cfg.num_test_patterns = 200;
    endfunction
endclass
```

---

## 📚 Documentation

| Document | Description |
|---------|-------------|
| [Getting Started](GETTING_STARTED.md) | Step-by-step onboarding path |
| [Architecture Guide](docs/ARCHITECTURE.md) | Detailed architecture and design |
| [User Guide](docs/USER_GUIDE.md) | Comprehensive usage guide |
| [API Reference](docs/API_REFERENCE.md) | Complete API documentation |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common problems and validated fixes |
| [Best Practices](docs/BEST_PRACTICES.md) | Team recommendations and guardrails |
| [Design Document](docs/DESIGN_DOCUMENT.md) | Technical rationale and maintainability strategy |
| [Knowledge Base](docs/KNOWLEDGE_BASE.md) | FAQ, snippets, decisions, and lessons learned |
| [Maintenance Process](docs/MAINTENANCE_PROCESS.md) | Quarterly review, ownership, and update triggers |
| [CI/CD Pipeline](docs/CI_CD_PIPELINE.md) | Automation flow, sign-off gates, and deployment procedure |
| [Portfolio Summary](Documentation/PORTFOLIO_PROJECT_SUMMARY.md) | Interview-ready project summary and key outcomes |
| [Documentation Hub](Documentation/README.md) | Full technical index (tapeout, analytics, handoff, roadmap) |
| [JTAG Agent Docs](uvm_tb/agents/jtag/JTAG_AGENT_DOCUMENTATION.md) | IEEE 1149.1 JTAG agent reference |
| [Setup Guide](SETUP.md) | Environment setup instructions |

### Documentation Search (Local)

```bash
python scripts/generate_doc_index.py
python scripts/doc_search.py "fault coverage"
```

---

## 🛠️ Makefile Commands

```bash
make help              # Show all targets
make compile           # Compile testbench
make run               # Run simulation
make clean             # Clean build artifacts
make stil_example      # Generate example STIL
make validate          # Validate project structure
make parse_atpg        # Parse ATPG file
```

---

## 🔧 Extension Points

The framework is designed for extensibility:

- **New Agents**: Add under `uvm_tb/agents/`
- **New Sequences**: Add under `uvm_tb/sequences/`
- **New Tests**: Extend `base_test` class
- **New ATPG Formats**: Extend `atpg_parser.py`

---

## 🐛 Troubleshooting

| Issue | Solution |
|------|----------|
| Interface not found | Set interfaces in config database in `tb_top.sv` |
| STIL not generated | Check `cfg.stil_enable_generation = 1` |
| Compilation errors | Verify UVM library path in Makefile |
| Simulation hangs | Check for missing objections in test |

For more details, see [User Guide](docs/USER_GUIDE.md).

---

## Week 3 production deliverables

End-to-end bundle: **compression metrics**, **at-speed timing report**, **formal/DRC JSON**, **HTML/CSV/JSON reports**, **failure analysis**, and **`production_readiness_checklist.json`**.

```bash
set PYTHONPATH=python
python python/integrated_flow/week3_production.py --atpg patterns/stuck_at.stil --out deliverables --tck-mhz 200
```

- **Guide:** [Documentation/WEEK3_PRODUCTION.md](Documentation/WEEK3_PRODUCTION.md)
- **GPU specialization guide:** [Documentation/GPU_SHADER_DFT_SPECIALIZATION.md](Documentation/GPU_SHADER_DFT_SPECIALIZATION.md)
- **Multi-core cache/interconnect guide:** [Documentation/MULTI_CORE_CACHE_INTERCONNECT_DFT.md](Documentation/MULTI_CORE_CACHE_INTERCONNECT_DFT.md)
- **Deliverables layout:** [deliverables/README.md](deliverables/README.md)
- **CI:** [.github/workflows/dft_week3.yml](.github/workflows/dft_week3.yml) (dry-run artifact)

---

## 👤 Maintainer

Maintained by **Raghuveer**.

- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`

---

## 📄 License

This framework is provided as-is for DFT verification purposes.
