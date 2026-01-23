# Makefile for DFT-STIL Verification Framework
# Supports VCS, QuestaSim, and Xcelium simulators

# Default simulator
SIMULATOR ?= vcs

# Project directories
UVM_TB_DIR = ../uvm_tb
PYTHON_DIR = ../python
CONFIG_DIR = ../config
EXAMPLES_DIR = ../examples

# UVM library path (adjust based on installation)
UVM_HOME ?= $(QUESTA_HOME)/verilog_src/uvm-1.2

# Source files
UVM_SOURCES = $(UVM_TB_DIR)/dft_tb_pkg.sv \
              $(UVM_TB_DIR)/tb_top.sv \
              $(EXAMPLES_DIR)/example_dut_wrapper.sv

# Compiler flags
VCS_FLAGS = -sverilog -timescale=1ns/1ps +incdir+$(UVM_TB_DIR) +incdir+$(UVM_HOME)/src \
            $(UVM_HOME)/src/uvm.sv -full64 -debug_access+all -lca -kdb

QUESTA_FLAGS = -sv -timescale 1ns/1ps +incdir+$(UVM_TB_DIR) +incdir+$(UVM_HOME)/src \
               -work work -voptargs=+acc

XCELIUM_FLAGS = -sv -timescale 1ns/1ps +incdir+$(UVM_TB_DIR) +incdir+$(UVM_HOME)/src \
                -work work -access +rwc

# Test configuration
TEST_NAME ?= base_test
CONFIG_FILE ?= $(CONFIG_DIR)/test_config.json

# Waveform options
WAVEFORM ?= fsdb
DUMP_FILE ?= tb_top.$(WAVEFORM)

# Default target
all: compile run

# Compile based on simulator
compile:
	@echo "Compiling with $(SIMULATOR)..."
ifeq ($(SIMULATOR),vcs)
	vcs $(VCS_FLAGS) $(UVM_SOURCES) -o simv
else ifeq ($(SIMULATOR),questa)
	vlog $(QUESTA_FLAGS) $(UVM_SOURCES)
	vopt +acc work.tb_top -o tb_top_opt
else ifeq ($(SIMULATOR),xcelium)
	xmvlog $(XCELIUM_FLAGS) $(UVM_SOURCES)
	xmelab $(XCELIUM_FLAGS) work.tb_top
endif

# Run simulation
run:
	@echo "Running test: $(TEST_NAME)"
ifeq ($(SIMULATOR),vcs)
	./simv +UVM_TESTNAME=$(TEST_NAME) +UVM_VERBOSITY=UVM_MEDIUM +vcd+$(DUMP_FILE)
else ifeq ($(SIMULATOR),questa)
	vsim -c work.tb_top_opt -do "run -all; quit -f" +UVM_TESTNAME=$(TEST_NAME)
else ifeq ($(SIMULATOR),xcelium)
	xmsim -run work.tb_top +UVM_TESTNAME=$(TEST_NAME)
endif

# Clean build artifacts
clean:
	rm -rf simv simv.daidir csrc ucli.key vc_hdrs.h
	rm -rf work transcript vsim.wlf
	rm -rf xcelium.d xrun.log xrun.history
	rm -rf *.vcd *.fsdb *.log
	rm -rf output.stil

# Generate STIL example
stil_example:
	@echo "Generating example STIL file..."
	python3 $(PYTHON_DIR)/stil_generator/stil_template_generator.py $(EXAMPLES_DIR)/example_pattern.stil

# Validate project structure
validate:
	@echo "Validating project structure..."
	python3 $(PYTHON_DIR)/validators/file_validator.py

# Parse ATPG file
parse_atpg:
	@echo "Parsing ATPG file..."
	@if [ -z "$(ATPG_FILE)" ] || [ -z "$(ATPG_FORMAT)" ]; then \
		echo "Usage: make parse_atpg ATPG_FILE=<file> ATPG_FORMAT=<format>"; \
		echo "Formats: tetramax, fastscan, encounter"; \
		exit 1; \
	fi
	python3 $(PYTHON_DIR)/atpg_parser/atpg_parser.py $(ATPG_FORMAT) $(ATPG_FILE)

# Help target
help:
	@echo "DFT-STIL Verification Framework Makefile"
	@echo ""
	@echo "Usage: make [target] [options]"
	@echo ""
	@echo "Targets:"
	@echo "  all              - Compile and run (default)"
	@echo "  compile          - Compile testbench"
	@echo "  run              - Run simulation"
	@echo "  clean            - Clean build artifacts"
	@echo "  stil_example     - Generate example STIL file"
	@echo "  validate         - Validate project structure"
	@echo "  parse_atpg       - Parse ATPG file"
	@echo "  help             - Show this help message"
	@echo ""
	@echo "Options:"
	@echo "  SIMULATOR=vcs|questa|xcelium  - Select simulator (default: vcs)"
	@echo "  TEST_NAME=<name>              - UVM test name (default: base_test)"
	@echo "  WAVEFORM=vcd|fsdb             - Waveform format (default: fsdb)"
	@echo ""
	@echo "Examples:"
	@echo "  make SIMULATOR=questa TEST_NAME=my_test"
	@echo "  make parse_atpg ATPG_FILE=patterns.atpg ATPG_FORMAT=tetramax"

.PHONY: all compile run clean stil_example validate parse_atpg help
