// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: GPL-3.0-or-later

`timescale 1ns/1ps
`default_nettype none

module icebreaker_top (
    input  logic CLK,

    input  logic BTN_N,
    output logic LEDR_N,
    output logic LEDG_N,

    // PMOD DVI
    output logic       dvi_clk,    // DVI pixel clock
    output logic       dvi_hsync,  // DVI horizontal sync
    output logic       dvi_vsync,  // DVI vertical sync
    output logic       dvi_de,     // DVI data enable
    output logic [3:0] dvi_r,      // 4-bit DVI red
    output logic [3:0] dvi_g,      // 4-bit DVI green
    output logic [3:0] dvi_b       // 4-bit DVI blue
);

    logic pixel_clk;
    logic locked;
    logic reset_n;

    // Given input frequency:        12.000 MHz
    // Requested output frequency:   40.000 MHz
    // Achieved output frequency:    39.750 MHz

    SB_PLL40_PAD #(
		.FEEDBACK_PATH("SIMPLE"),
		.DIVR(4'b0000),		// DIVR =  0
		.DIVF(7'b0110100),	// DIVF = 52
		.DIVQ(3'b100),		// DIVQ =  4
		.FILTER_RANGE(3'b001)	// FILTER_RANGE = 1
	) uut (
		.LOCK(locked),
		.RESETB(1'b1),
		.BYPASS(1'b0),
		.PACKAGEPIN(CLK),
		.PLLOUTCORE(pixel_clk)
	);

    assign reset_n = BTN_N && locked;
    
    logic [24-1:0] counter;
    
    always_ff @(posedge pixel_clk, negedge reset_n) begin
        if (!reset_n) begin
            counter <= '0;
        end else begin
            counter <= counter + 1;
        end
    end
    
    assign LEDR_N = counter[24-1];
    assign LEDG_N = !counter[24-1];

    logic [5:0] rrggbb;
    logic hsync;
    logic vsync;
    logic hblank;
    logic vblank;
    logic de;

    top top_inst (
        .clk        (pixel_clk), // 40 MHz
        .reset_n    (reset_n),

        // SPI signals
        .spi_sclk (1'b0),
        .spi_mosi (1'b0),
        .spi_miso (),
        .spi_cs   (1'b0),

        // SVGA signals
        .rrggbb         (rrggbb),
        .hsync          (hsync),
        .vsync          (vsync),
        .next_vertical  (),
        .next_frame     (),
        .hblank         (hblank),
        .vblank         (vblank),
        .de             (de)
    );

    logic [ 3: 0] paint_r;
    logic [ 3: 0] paint_g;
    logic [ 3: 0] paint_b;

    assign paint_r     = {rrggbb[5], {3{rrggbb[4]}}};
    assign paint_g     = {rrggbb[3], {3{rrggbb[2]}}};
    assign paint_b     = {rrggbb[1], {3{rrggbb[0]}}};

    // DVI Pmod output
    SB_IO #(
        .PIN_TYPE(6'b010100)  // PIN_OUTPUT_REGISTERED
    ) dvi_signal_io[14:0] (
        .PACKAGE_PIN({dvi_hsync, dvi_vsync, dvi_de, dvi_r, dvi_g, dvi_b}),
        .OUTPUT_CLK(pixel_clk),
        .D_OUT_0({hsync, vsync, de, paint_r, paint_g, paint_b}),
        .D_OUT_1()
    );

    // DVI Pmod clock output: 180° out of phase with other DVI signals
    SB_IO #(
        .PIN_TYPE(6'b010000)  // PIN_OUTPUT_DDR
    ) dvi_clk_io (
        .PACKAGE_PIN(dvi_clk),
        .OUTPUT_CLK(pixel_clk),
        .D_OUT_0(1'b0),
        .D_OUT_1(1'b1)
    );

endmodule
