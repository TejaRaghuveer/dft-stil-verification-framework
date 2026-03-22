/**
 * Optional macros linking assertions to protocol / timing requirements.
 * Include after `uvm_macros.svh in tests that log pattern context.
 */
`ifndef DFT_ASSERTION_MACROS_SVH
`define DFT_ASSERTION_MACROS_SVH

// Log UVM message with pattern + vector index when a concurrent assertion would fire
`define DFT_ASSERT_PROTOCOL(cond, pattern_id, vec_id, msg) \
  begin \
    if (!(cond)) begin \
      `uvm_error("DFT_ASSERT", $sformatf("[%s vec=%0d] %s: %s", pattern_id, vec_id, "IEEE1149.1", msg)) \
    end \
  end

`define DFT_ASSERT_TIMING(cond, pattern_id, vec_id, msg) \
  begin \
    if (!(cond)) begin \
      `uvm_error("DFT_TIMING", $sformatf("[%s vec=%0d] %s", pattern_id, vec_id, msg)) \
    end \
  end

`endif
