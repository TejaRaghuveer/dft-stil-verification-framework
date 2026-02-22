/**
 * Pad Driver/Monitor Utilities
 *
 * Converts between logic vectors, integers, and hex strings for pad data.
 */

class pad_utils;
    
    /**
     * Convert logic vector to integer (up to 64 bits).
     * @param vec Logic vector (indexed 0 to size-1, LSB = 0)
     * @return Integer value
     */
    static function int logic_vec_to_int(const ref logic vec[]);
        int val = 0;
        for (int i = 0; i < vec.size() && i < 32; i++) begin
            if (vec[i]) val |= (1 << i);
        end
        return val;
    endfunction

    /**
     * Convert integer to logic vector (LSB first).
     * @param val Integer value
     * @param width Number of bits
     * @param vec Output logic vector (must be pre-allocated)
     */
    static function void int_to_logic_vec(input int val, input int width, ref logic vec[]);
        vec = new[width];
        for (int i = 0; i < width; i++) begin
            vec[i] = (val >> i) & 1;
        end
    endfunction

    /**
     * Convert hex string to logic vector (e.g., "A5" -> 10100101, MSB first in string).
     * @param hex_str Hex string (0-9, A-F, a-f)
     * @param vec Output logic vector (allocated inside)
     */
    static function void hex_string_to_logic_vec(input string hex_str, ref logic vec[]);
        int len = hex_str.len();
        int bits = len * 4;
        vec = new[bits];
        for (int i = 0; i < len; i++) begin
            int nibble;
            int c = hex_str.getc(i);
            if (c >= 48 && c <= 57) nibble = c - 48;       // '0'-'9'
            else if (c >= 65 && c <= 70) nibble = c - 65 + 10;  // 'A'-'F'
            else if (c >= 97 && c <= 102) nibble = c - 97 + 10; // 'a'-'f'
            else nibble = 0;
            vec[i*4 + 0] = (nibble >> 0) & 1;
            vec[i*4 + 1] = (nibble >> 1) & 1;
            vec[i*4 + 2] = (nibble >> 2) & 1;
            vec[i*4 + 3] = (nibble >> 3) & 1;
        end
    endfunction

    /**
     * Convert logic vector to hex string (LSB in vec[0], lower nibble first in hex).
     * @param vec Logic vector
     * @return Hex string (e.g., "A5F3")
     */
    static function string logic_vec_to_hex_string(const ref logic vec[]);
        string hex = "";
        int sz = vec.size();
        for (int i = 0; i < sz; i += 4) begin
            int nibble = 0;
            for (int j = 0; j < 4 && (i+j) < sz; j++)
                if (vec[i+j]) nibble |= (1 << j);
            hex = { hex, $sformatf("%0X", nibble) };
        end
        return hex;
    endfunction

    /**
     * Format pad data: fill logic vector from integer value (for use with pad_out).
     * @param val Integer value
     * @param width Bit width
     * @param pad_bits Output to drive (e.g., slice of pad_out)
     */
    static function void format_pad_data_from_int(input longint val, input int width, ref logic pad_bits[]);
        pad_bits = new[width];
        for (int i = 0; i < width; i++) begin
            pad_bits[i] = (val >> i) & 1;
        end
    endfunction

    /**
     * Format pad data: get integer from current pad bits (e.g., from pad_in).
     * @param pad_bits Logic vector from interface
     * @param width Bit width
     * @return Integer value
     */
    static function longint format_pad_data_to_int(const ref logic pad_bits[], input int width);
        longint val = 0;
        for (int i = 0; i < width; i++) begin
            if (pad_bits[i]) val |= (1'b1 << i);
        end
        return val;
    endfunction

endclass
