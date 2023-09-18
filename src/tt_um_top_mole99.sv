// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: GPL-3.0-or-later

`timescale 1ns/1ps
`default_nettype none

module tt_um_top_mole99 (
    input  wire [7:0] ui_in,    // Dedicated inputs - connected to the input switches
    output wire [7:0] uo_out,   // Dedicated outputs - connected to the 7 segment display
    input  wire [7:0] uio_in,   // IOs: Bidirectional Input path
    output wire [7:0] uio_out,  // IOs: Bidirectional Output path
    output wire [7:0] uio_oe,   // IOs: Bidirectional Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    assign uio_oe = 8'b11111111;
    assign uio_out[7:1] = 7'b0000000;

    top top_inst (
        .clk        (clk),
        .reset_n    (rst_n && ena),

        // SPI signals
        .spi_clk    (ui_in[0]),
        .spi_data   (ui_in[1]),

        // SVGA signals
        .rrggbb     (uo_out[7:2]),
        .hsync      (uo_out[0]),
        .vsync      (uo_out[1]),
        .next_frame (uio_out[0])
    );

endmodule
