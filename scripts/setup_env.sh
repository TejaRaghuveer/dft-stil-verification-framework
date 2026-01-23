#!/bin/bash
#
# Environment Setup Script
# Sets up environment variables for DFT-STIL verification framework
#

echo "DFT-STIL Verification Framework - Environment Setup"
echo "===================================================="

# Detect simulator
if [ -n "$VCS_HOME" ]; then
    echo "Detected VCS: $VCS_HOME"
    export SIMULATOR=vcs
elif [ -n "$QUESTA_HOME" ]; then
    echo "Detected QuestaSim: $QUESTA_HOME"
    export SIMULATOR=questa
elif [ -n "$CDS_HOME" ]; then
    echo "Detected Xcelium: $CDS_HOME"
    export SIMULATOR=xcelium
else
    echo "Warning: No simulator detected. Please set VCS_HOME, QUESTA_HOME, or CDS_HOME"
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "Python: $PYTHON_VERSION"
else
    echo "Warning: Python 3 not found"
fi

# Check UVM
if [ -n "$UVM_HOME" ]; then
    echo "UVM Home: $UVM_HOME"
else
    echo "Warning: UVM_HOME not set. UVM library path may need to be configured."
fi

echo "===================================================="
echo "Environment setup complete"
echo ""
echo "To use this environment, source this script:"
echo "  source scripts/setup_env.sh"
