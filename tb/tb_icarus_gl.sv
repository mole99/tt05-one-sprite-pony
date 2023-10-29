// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: Apache-2.0

`timescale 1ns/1ps
`default_nettype none

module tb;

    logic clk = 1'b0;
    logic reset_n = 1'b0;
    logic ena = 1'b0;
    
    logic [5:0] rrggbb;
    logic hsync;
    logic vsync;
    
    logic [7:0] ui_in = '0;
    logic [7:0] uio_in = '0;
        
    logic [7:0] uo_out;
    logic [7:0] uio_out;
    logic [7:0] uio_oe;

    tt_um_top_mole99 tt_um_top_mole99_i (
        .VPWR   (1'b1),
        .VGND   (1'b0),
    
        .ui_in,
        .uo_out,
        .uio_in,
        .uio_out,
        .uio_oe,

        .ena,
        .clk    (clk),
        .rst_n  (reset_n)
    );

    always #20 clk = !clk;

    initial begin
        $dumpfile("tb_gl.fst");
        $dumpvars(0, tb);
        
        #80;
        reset_n = 1'b1;
        #40;
        ena = 1'b1;
        #100000000;
        $finish;
    end
    
    assign rrggbb = {uo_out[0], uo_out[4], uo_out[1], uo_out[5], uo_out[2], uo_out[6]};
    assign hsync = uo_out[7];
    assign vsync = uo_out[3];

endmodule
