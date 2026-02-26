/**
 * Legacy STIL Subscriber (Adapter)
 *
 * This component remains as the connection point used by the existing
 * environment (`test_env`). It adapts JTAG transactions to the
 * more general `stil_generator` / `stil_info_transaction` API.
 */

class stil_subscriber extends uvm_subscriber#(jtag_transaction);
    
    `uvm_component_utils(stil_subscriber)
    
    // Underlying core generator
    stil_generator gen;
    
    function new(string name = "stil_subscriber", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        gen = stil_generator::type_id::create("stil_gen", this);
    endfunction
    
    // Adapt JTAG transactions into stil_info_transaction and forward
    function void write(jtag_transaction t);
        stil_info_transaction sti;
        sti = stil_info_transaction::type_id::create("sti_tr");
        sti.vector_index = gen.vector_count;
        sti.cycle_time   = $time;

        // Map basic JTAG pins into STIL signal values
        sti.add_signal_value("TCK", "1"); // conceptual TCK high during sample
        sti.add_signal_value("TMS", t.tms ? "1" : "0");
        sti.add_signal_value("TDI", t.tdi ? "1" : "0");
        if (t.tdo_valid)
            sti.add_compare_value("TDO", t.tdo_expected ? "1" : "0");
        else
            sti.add_signal_value("TDO", "X");

        gen.write(sti);
    endfunction

endclass
