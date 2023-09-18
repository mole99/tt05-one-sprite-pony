// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: GPL-3.0-or-later

`timescale 1ns/1ps

module timing #(
    parameter RESOLUTION,
    parameter FRONT_PORCH,
    parameter SYNC_PULSE,
    parameter BACK_PORCH
)(
    input  logic clk,      // clock
    input  logic enable,   // enable counting
    input  logic reset_n,  // reset counter
    output logic sync,     // 1'b1 if in sync region
    output logic blank,    // 1'b1 if in blank region
    output logic next,     // 1'b1 if max value is reached
    output logic signed [$clog2(RESOLUTION + FRONT_PORCH + SYNC_PULSE + BACK_PORCH) : 0] counter    // counter value
);
    // Total cycles to count
    //localparam TOTAL = RESOLUTION + FRONT_PORCH + SYNC_PULSE + BACK_PORCH;

    // The reset value for the counter
    localparam signed RESET = -FRONT_PORCH - SYNC_PULSE - BACK_PORCH;

    // Signal to trigger next counter in the chain
    assign next = counter == RESOLUTION - 1 && enable;

    // Counter logic
    always_ff @(posedge clk, negedge reset_n) begin
        if (!reset_n) begin
            counter <= RESET;
        end else begin
            if (enable) begin
                counter <= counter + 1;
                if (next) begin
                    counter <= RESET;
                end
            end
        end
    end
    
    assign sync = counter >= -SYNC_PULSE - BACK_PORCH && counter < -BACK_PORCH;
    assign blank = counter >= -FRONT_PORCH - SYNC_PULSE - BACK_PORCH && counter < 0;

endmodule
