# Simple DFT UVM Makefile
#
# Usage examples:
#   make sim SIM=vcs TEST=scan_shift_test
#   make sim SIM=xrun TEST=full_regression_test
#
# Variables:
#   SIM  : vcs | xrun  (default: vcs)
#   TEST : UVM test class name (default: simple_jtag_test)

SIM      ?= vcs
TEST     ?= simple_jtag_test
PLUSARGS ?=

TOP      = tb_top
PKG_FILE = uvm_tb/dft_tb_pkg.sv

all: sim

sim:
ifeq ($(SIM),vcs)
	@echo "Compiling and running with VCS..."
	vcs -full64 -sverilog +vpi +acc \
	    +define+UVM_NO_DEPRECATED \
	    +incdir+. \
	    $(PKG_FILE) uvm_tb/tb_top.sv \
	    -top $(TOP) \
	    -l vcs_compile.log
	./simv +UVM_TESTNAME=$(TEST) $(PLUSARGS) +vcd -l vcs_sim.log
else ifeq ($(SIM),xrun)
	@echo "Compiling and running with Xcelium (xrun)..."
	xrun -64bit -uvm \
	     +define+UVM_NO_DEPRECATED \
	     +incdir+. \
	     $(PKG_FILE) uvm_tb/tb_top.sv \
	     -top $(TOP) \
	     +UVM_TESTNAME=$(TEST) $(PLUSARGS) +vcd \
	     -l xrun.log
else
	@echo "Unknown SIM=$(SIM). Supported: vcs, xrun."
	exit 1
endif

clean:
	rm -rf simv simv.daidir csrc *.log *.vcd xrun.history xcelium.d

