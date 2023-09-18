// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: GPL-3.0-or-later

`timescale 1ns/1ps

module sprite #(
    parameter WIDTH,
    parameter HEIGHT
)(
    input  logic clk,      // clock
    input  logic reset_n,  // reset 
    input  logic shiftf,    // shift sprite data
    input  logic shiftb,    // shift sprite data
    output logic data_out,      // pixel data
    input  logic load,
    input  logic data_in
);

    `define INIT_SPRITE

    logic [WIDTH*HEIGHT-1 : 0] sprite_data;

    always_ff @(posedge clk, negedge reset_n) begin
        if (!reset_n) begin

            `ifdef INIT_SPRITE
            sprite_data <= '0;
            sprite_data[ 9: 0] <= 10'b0011111100;
            sprite_data[19:10] <= 10'b0110000010;
            sprite_data[29:20] <= 10'b1100111111;
            sprite_data[39:30] <= 10'b1000001000;
            sprite_data[49:40] <= 10'b1011111001;
            sprite_data[59:50] <= 10'b1000101001;
            sprite_data[69:60] <= 10'b1000101001;
            sprite_data[79:70] <= 10'b1100100011;
            sprite_data[89:80] <= 10'b0110100110;
            sprite_data[99:90] <= 10'b0000111100;
            
            `endif
        end else begin
            if (shiftf) begin
                if (!load) begin
                    sprite_data <= {sprite_data[0], sprite_data[WIDTH*HEIGHT-1:1]};
                end else begin
                    sprite_data <= {data_in, sprite_data[WIDTH*HEIGHT-1:1]};
                end
                
            end
            if (shiftb) begin
                sprite_data <= {sprite_data[WIDTH*HEIGHT-2:0], sprite_data[WIDTH*HEIGHT-1]};
            end
        end
    end
    
    assign data_out = sprite_data[0];

endmodule
