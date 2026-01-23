#!/bin/bash
#
# Simulation Runner Script
# Provides a convenient wrapper for running simulations with different simulators
#

set -e

# Default values
SIMULATOR="vcs"
TEST_NAME="base_test"
VERBOSITY="UVM_MEDIUM"
WAVEFORM="fsdb"
CONFIG_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--simulator)
            SIMULATOR="$2"
            shift 2
            ;;
        -t|--test)
            TEST_NAME="$2"
            shift 2
            ;;
        -v|--verbosity)
            VERBOSITY="$2"
            shift 2
            ;;
        -w|--waveform)
            WAVEFORM="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -s, --simulator <sim>    Simulator: vcs, questa, xcelium (default: vcs)"
            echo "  -t, --test <name>        UVM test name (default: base_test)"
            echo "  -v, --verbosity <level> UVM verbosity (default: UVM_MEDIUM)"
            echo "  -w, --waveform <format> Waveform format: vcd, fsdb (default: fsdb)"
            echo "  -c, --config <file>      Configuration file path"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set up environment based on simulator
case $SIMULATOR in
    vcs)
        if [ -z "$VCS_HOME" ]; then
            echo "Error: VCS_HOME not set"
            exit 1
        fi
        ;;
    questa)
        if [ -z "$QUESTA_HOME" ]; then
            echo "Error: QUESTA_HOME not set"
            exit 1
        fi
        ;;
    xcelium)
        if [ -z "$CDS_HOME" ]; then
            echo "Error: CDS_HOME not set"
            exit 1
        fi
        ;;
    *)
        echo "Error: Unknown simulator: $SIMULATOR"
        exit 1
        ;;
esac

echo "=========================================="
echo "DFT-STIL Verification Framework"
echo "=========================================="
echo "Simulator: $SIMULATOR"
echo "Test: $TEST_NAME"
echo "Verbosity: $VERBOSITY"
echo "Waveform: $WAVEFORM"
echo "=========================================="

# Run simulation using Makefile
make SIMULATOR=$SIMULATOR TEST_NAME=$TEST_NAME WAVEFORM=$WAVEFORM run

echo "=========================================="
echo "Simulation completed"
echo "=========================================="
