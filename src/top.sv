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

    /* verilator lint_off WIDTH */
    
    logic signed [$clog2(HTOTAL) : 0] counter_h;
    logic signed [$clog2(VTOTAL) : 0] counter_v;
    
    logic next_vertical;
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

    logic signed [$clog2(HTOTAL) - 3 : 0] counter_h_small;
    logic signed [$clog2(VTOTAL) - 3 : 0] counter_v_small;

    assign counter_h_small = counter_h[$clog2(HTOTAL) : 3];
    assign counter_v_small = counter_v[$clog2(VTOTAL) : 3];
    
    /*
        Sprite
    */

    localparam SPRITE_WIDTH = 10;
    localparam SPRITE_HEIGHT = 10;
    
    logic sprite_pixel;
    logic [7:0] sprite_x;
    logic [7:0] sprite_y;
    
    logic sprite_x_dir;
    logic sprite_y_dir;
    
    //logic wall_hit;
    //assign wall_hit = 
    
    // Sprite movement logic
    always_ff @(posedge clk, negedge reset_n) begin
        if (!reset_n) begin
            sprite_x <= '0;
            sprite_y <= '0;
            sprite_x_dir <= '0;
            sprite_y_dir <= '0;
        end else begin
            if (next_frame) begin
                if (sprite_x_dir == 1'b0) begin
                    sprite_x <= sprite_x + 1;
                    
                    if (sprite_x == WIDTH_SMALL - SPRITE_WIDTH - 1) begin
                        sprite_x_dir <= 1;
                    end
                end else begin
                    sprite_x <= sprite_x - 1;
                    
                    if (sprite_x == 1) begin
                        sprite_x_dir <= 0;
                    end
                end
   
                if (sprite_y_dir == 1'b0) begin
                    sprite_y <= sprite_y + 1;
                    
                    if (sprite_y == HEIGHT_SMALL - SPRITE_HEIGHT - 1) begin
                        sprite_y_dir <= 1;
                    end
                end else begin
                    sprite_y <= sprite_y - 1;
                    
                    if (sprite_y == 1) begin
                        sprite_y_dir <= 0;
                    end
                end
            end
        end
    end
    
    // Sprite access/drawing logic
    logic sprite_enable;
    logic sprite_shiftf;
    logic sprite_shiftb;
    
    logic sprite_is_vertical;
    logic sprite_is_horizontal;
    
    assign sprite_is_vertical = counter_v_small >= sprite_y && counter_v_small < (sprite_y + SPRITE_HEIGHT);
    assign sprite_is_horizontal = counter_h_small >= sprite_x && counter_h_small < (sprite_x + SPRITE_WIDTH);
    
    // Always access the sprite at the end of a big pixel
    logic sprite_access;
    assign sprite_access = &counter_h[2:0];
    
    logic sprite_is_horizontal_before;
    assign sprite_is_horizontal_before = counter_h_small >= ($signed(sprite_x) - SPRITE_WIDTH) && counter_h_small < $signed(sprite_x);
    
    assign sprite_enable = sprite_is_horizontal && sprite_is_vertical;
    
    // Shift during the pixel
    assign sprite_shiftf = sprite_is_horizontal && sprite_is_vertical;
    
    // Don't shift back before the first line so that we get the next pixel
    assign sprite_shiftb = sprite_is_horizontal_before && sprite_is_vertical && (counter_v[2:0] != 0);

    sprite #(
        .WIDTH  (SPRITE_WIDTH),
        .HEIGHT (SPRITE_HEIGHT)
    ) sprite_inst (
        .clk        (clk),
        .reset_n    (reset_n),
        .shiftf      ((sprite_shiftf && sprite_access) || spi_clk_edge),
        .shiftb      ((sprite_shiftb && sprite_access)),
        .data_out    (sprite_pixel),
        .data_in     (spi_data_sync),
        .load        (spi_clk_edge)
    );
    
    /*
        Colors
    */

    always_comb begin
        rrggbb = BACKGROUND_COLOR;
        
        if (sprite_pixel && sprite_enable) begin
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
