/**
 * JTAG TAP protocol assertions for simulation and formal (IEEE 1149.1).
 *
 * Enum encoding MUST match uvm_tb/agents/jtag/jtag_transaction.sv (jtag_state_t).
 *
 * Usage (example):
 *   jtag_tap_formal_props #(
 *     .REGISTER_TDO_CHECK(1)
 *   ) u_props (
 *     .tck   (jtag_if_inst.tck),
 *     .tms   (jtag_if_inst.tms),
 *     .tdi   (jtag_if_inst.tdi),
 *     .tdo   (jtag_if_inst.tdo),
 *     .trst_n(jtag_if_inst.trst_n)
 *   );
 *
 * For formal, constrain inputs and reset; bind under `ifdef DFT_FORMAL.
 */

`ifndef JTAG_TAP_FORMAL_SVA_SV
`define JTAG_TAP_FORMAL_SVA_SV

`timescale 1ns/1ps

module jtag_tap_formal_props #(
    parameter bit REGISTER_TDO_CHECK = 1
)(
    input logic tck,
    input logic tms,
    input logic tdi,
    input logic tdo,
    input logic trst_n
);

    // Mirror jtag_state_t order in jtag_transaction.sv
    typedef enum int {
        TEST_LOGIC_RESET,
        RUN_TEST_IDLE,
        SELECT_DR_SCAN,
        CAPTURE_DR,
        SHIFT_DR,
        EXIT1_DR,
        PAUSE_DR,
        EXIT2_DR,
        UPDATE_DR,
        SELECT_IR_SCAN,
        CAPTURE_IR,
        SHIFT_IR,
        EXIT1_IR,
        PAUSE_IR,
        EXIT2_IR,
        UPDATE_IR
    } tap_state_e;

    tap_state_e cs;

    function automatic tap_state_e tap_next(tap_state_e cur, logic tm);
        case (cur)
            TEST_LOGIC_RESET: return tm ? TEST_LOGIC_RESET : RUN_TEST_IDLE;
            RUN_TEST_IDLE:    return tm ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            SELECT_DR_SCAN:   return tm ? SELECT_IR_SCAN : CAPTURE_DR;
            CAPTURE_DR:       return tm ? EXIT1_DR : SHIFT_DR;
            SHIFT_DR:         return tm ? EXIT1_DR : SHIFT_DR;
            EXIT1_DR:         return tm ? UPDATE_DR : PAUSE_DR;
            PAUSE_DR:         return tm ? EXIT2_DR : PAUSE_DR;
            EXIT2_DR:         return tm ? UPDATE_DR : SHIFT_DR;
            UPDATE_DR:        return tm ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            SELECT_IR_SCAN:   return tm ? TEST_LOGIC_RESET : CAPTURE_IR;
            CAPTURE_IR:       return tm ? EXIT1_IR : SHIFT_IR;
            SHIFT_IR:         return tm ? EXIT1_IR : SHIFT_IR;
            EXIT1_IR:         return tm ? UPDATE_IR : PAUSE_IR;
            PAUSE_IR:         return tm ? EXIT2_IR : PAUSE_IR;
            EXIT2_IR:         return tm ? UPDATE_IR : SHIFT_IR;
            UPDATE_IR:        return tm ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            default:          return TEST_LOGIC_RESET;
        endcase
    endfunction

    always_ff @(posedge tck or negedge trst_n) begin
        if (!trst_n)
            cs <= TEST_LOGIC_RESET;
        else
            cs <= tap_next(cs, tms);
    end

    // TAP step: after each rising TCK, cs matches next state from prior cycle's cs and TMS
    property p_tap_step;
        @(posedge tck) disable iff (!trst_n)
            ##1 (cs == tap_next($past(cs), $past(tms)));
    endproperty

    generate
        if (REGISTER_TDO_CHECK) begin : g_tdo
            // Property 2: TDO not X during shift (bounded strobing)
            property p_tdo_known_shift;
                @(posedge tck) disable iff (!trst_n)
                    ((cs == SHIFT_DR) || (cs == SHIFT_IR)) |-> !$isunknown(tdo);
            endproperty
            assert property (p_tdo_known_shift)
                else $error("DFT_SVA: TDO unknown during shift state");
        end
    endgenerate

    assert property (p_tap_step)
        else $error("DFT_SVA: TAP transition inconsistent with TMS");

endmodule

`endif // JTAG_TAP_FORMAL_SVA_SV
