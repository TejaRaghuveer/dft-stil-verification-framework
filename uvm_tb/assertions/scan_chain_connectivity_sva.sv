/**
 * Scan chain connectivity templates (hierarchy-specific — adapt signal names).
 *
 * Example proof goals (formal):
 *   - In shift mode with SE asserted, TDI propagates to first flop SI.
 *   - Last flop SO muxes to TDO when in boundary-scan / internal scan mode.
 *
 * Instantiate per design after binding scan control signals.
 */

`ifndef SCAN_CHAIN_CONNECTIVITY_SVA_SV
`define SCAN_CHAIN_CONNECTIVITY_SVA_SV

`timescale 1ns/1ps

// Parameterized: chain length N, use generate in wrapper module in your TB
module scan_chain_connectivity_props #(
    parameter int N = 4
)(
    input logic tck,
    input logic scan_en,
    input logic tdi,
    input logic tdo,
    // Example: parallel observe of each scan cell output (DUT hooks)
    input logic [N-1:0] scan_so_bits
);

    // Property 3 (conceptual): serial equivalence — shift N cycles with known pattern
    property p_shift_propagation_stub;
        @(posedge tck)
            scan_en |-> strong(##[1:N] 1); // placeholder — replace with real SO chain check
    endproperty

    // In practice: assume ATPG shift sequence; prove each SO bit eventually reflects TDI stream
    // cover property (...);

endmodule

`endif
