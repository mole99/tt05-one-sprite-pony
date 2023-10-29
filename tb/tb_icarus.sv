// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: Apache-2.0

`timescale 1ns/1ps
`default_nettype none

module tb;

    logic clk = 1'b0;
    logic reset_n = 1'b0;
    logic [5:0] rrggbb;
    logic hsync;
    logic vsync;
    
    top top_inst (
            .clk,
            .reset_n,

            // SPI signals
            .spi_sclk   (1'b0),
            .spi_mosi   (1'b0),
            .spi_miso   (),
            .spi_cs     (1'b0),

            // SVGA signals
            .rrggbb,
            .hsync,
            .vsync,
            .next_vertical  (),
            .next_frame     ()
    );

    always #20 clk = !clk;

    initial begin
        $dumpfile("tb.fst");
        $dumpvars(0, tb);
        
        #80;
        reset_n = 1'b1;
        #100000000;
        $finish;
    end

endmodule
