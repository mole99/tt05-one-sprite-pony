// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: GPL-3.0-or-later

`timescale 1ns/1ps

module top (
    input  logic clk,
    input  logic reset_n,

    // SPI signals TODO
    input  logic spi_clk,
    input  logic spi_data,
    // TODO spi_sel

    // SVGA signals
    output logic [5:0] rrggbb,
    output logic hsync,
    output logic vsync,
    output logic next_vertical,
    output logic next_frame
);

    /*
        SVGA Timing for 800x600 60 Hz
        clock = 40 MHz or clock = 10 MHz TODO
    */

    localparam WIDTH    = 800;
    localparam HEIGHT   = 600;
    
    localparam HFRONT   = 40;
    localparam HSYNC    = 128;
    localparam HBACK    = 88;

    localparam VFRONT   = 1;
    localparam VSYNC    = 4;
    localparam VBACK    = 23;
    
    localparam HTOTAL = WIDTH + HFRONT + HSYNC + HBACK;
    localparam VTOTAL = HEIGHT + VFRONT + VSYNC + VBACK;
    
    logic signed [$clog2(HTOTAL) : 0] counter_h;
    logic signed [$clog2(VTOTAL) : 0] counter_v;
    
    logic hblank, vblank;

    localparam logic [5:0] BACKGROUND_COLOR = 6'b010101;
     
    // Horizontal timing
    timing #(
        .RESOLUTION     (WIDTH),
        .FRONT_PORCH    (HFRONT),
        .SYNC_PULSE     (HSYNC),
        .BACK_PORCH     (HBACK)
    ) timing_hor (
        .clk        (clk),
        .enable     (1'b1),
        .reset_n    (reset_n),
        .sync       (hsync),
        .blank      (hblank),
        .next       (next_vertical),
        .counter    (counter_h)
    );
    
    // Vertical timing
    timing #(
        .RESOLUTION     (HEIGHT),
        .FRONT_PORCH    (VFRONT),
        .SYNC_PULSE     (VSYNC),
        .BACK_PORCH     (VBACK)
    ) timing_ver (
        .clk        (clk),
        .enable     (next_vertical),
        .reset_n    (reset_n),
        .sync       (vsync),
        .blank      (vblank),
        .next       (next_frame),
        .counter    (counter_v)
    );
    
    /*
        Downscaling by factor of 8, i.e. one pixel is 8x8
    */

    localparam WIDTH_SMALL    = WIDTH / 8;
    localparam HEIGHT_SMALL   = HEIGHT / 8;

    /*
        Sprite drawing logic
        
        The sprite is implemented as one shift-register to save on resources.
        If we were rendering at the normal resolution of 800x600, we would simply shift the sprite by one when we needed new pixel data.
        However, since our internal resolution is 100x75, one sprite pixel is actually 8x8 real pixels.
        This means that we need to access the same sprite data for 8 rows in a row.
        
        One solution would be to have a bidirectional shift register, where in 7 out of 8 rows we first shift the data back before reading the sprite data.
        This would drastically increase resources since each flipflop would need a mux2 on its data input.
        
        The solution used here is to have the first row of the 8x8 pixel read the data from the sprite into a temporary shift register.
        This shift register is shifted as loaded when new horizontal sprite data is needed, but repeats automatically for the remaining 7 of 8 rows.
    */

    localparam SPRITE_WIDTH = 10;
    localparam SPRITE_HEIGHT = 10;
    
    logic [7:0] sprite_x;
    logic [7:0] sprite_y;
    
    sprite_movement #(
        .SPRITE_WIDTH  (SPRITE_WIDTH),
        .SPRITE_HEIGHT (SPRITE_HEIGHT),
        .WIDTH_SMALL   (WIDTH_SMALL),
        .HEIGHT_SMALL  (HEIGHT_SMALL)
    ) sprite_movement_inst (
        .clk        (clk),
        .reset_n    (reset_n),
        
        .next_frame (next_frame),
        
        .sprite_x   (sprite_x),
        .sprite_y   (sprite_y)
    );
    
    logic signed [$clog2(HTOTAL) - 3 : 0] counter_h_small;
    logic signed [$clog2(VTOTAL) - 3 : 0] counter_v_small;

    assign counter_h_small = counter_h[$clog2(HTOTAL) : 3];
    assign counter_v_small = counter_v[$clog2(VTOTAL) : 3];

    logic sprite_visible_v;
    logic sprite_visible_h;
    logic sprite_visible;
    
    assign sprite_visible_h = counter_h_small >= {1'b0, sprite_x} && counter_h_small < (sprite_x + SPRITE_WIDTH);
    assign sprite_visible_v = counter_v_small >= sprite_y && counter_v_small < (sprite_y + SPRITE_HEIGHT);
    assign sprite_visible = sprite_visible_h && sprite_visible_v;
    
    logic sprite_data;
    logic sprite_shift;
    
    sprite_data #(
        .WIDTH  (SPRITE_WIDTH),
        .HEIGHT (SPRITE_HEIGHT)
    ) sprite_data_inst (
        .clk        (clk),
        .reset_n    (reset_n),
        .shiftf     (sprite_shift || spi_clk_edge),
        .data_out   (sprite_data),
        .data_in    (spi_data_sync),
        .load       (spi_clk_edge)
    );
    
    logic sprite_pixel;
    
    sprite_access #(
        .WIDTH  (SPRITE_WIDTH)
    ) sprite_access_inst (
        .clk        (clk),

        .new_line       (counter_v[2:0] == 3'b000),
        .sprite_access  (counter_h[2:0] == 3'b111),
        
        .sprite_data    (sprite_data),
        .sprite_shift   (sprite_shift),

        .sprite_pixel   (sprite_pixel),
        .sprite_visible (sprite_visible)
    );
    
    /*
        Colors
    */

    always_comb begin
        rrggbb = BACKGROUND_COLOR;
        
        if (sprite_pixel && sprite_visible) begin
            rrggbb = 6'b111111;
        end
        
        if (hblank || vblank) begin
            rrggbb = '0;
        end
    end
    
    /*
        SPI
    */
    
    // Synchronizer to prevent metastability
    
    logic [1:0] spi_data_ff;
    
    always_ff @(posedge clk) begin
        spi_data_ff <= {spi_data_ff[0], spi_data};
    end
    
    logic spi_data_sync = spi_data_ff[1];
    
    // Detect edge
    
    logic spi_clk_delayed;

    always_ff @(posedge clk) begin
        spi_clk_delayed <= spi_clk;
    end
    
    logic spi_clk_edge;
    assign spi_clk_edge = !spi_clk_delayed && spi_clk;

endmodule
