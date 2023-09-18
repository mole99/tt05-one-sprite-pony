// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: GPL-3.0-or-later

`timescale 1ns/1ps

module sprite_access #(
    parameter WIDTH
)(
    input  logic clk,           // clock

    input  logic new_line,      // indicates the start of a new line of 8x8 pixels
    input  logic sprite_access, // always access sprite data at the end of a 8x8 pixel

    input  logic sprite_data,   // raw sprite data
    output logic sprite_shift,  // shift sprite by one

    output logic sprite_pixel,  // the pixel for the current position
    input  logic sprite_visible // is the sprite currently visible for this position
);

    // Shift sprite data upon the start of a new 8x8 pixel line
    assign sprite_shift = sprite_visible && sprite_access && new_line;

    // Temporary sprite line
    logic [WIDTH - 1: 0] sprite_line;

    always_ff @(posedge clk) begin
        // Shift data if sprite is visible
        if (sprite_visible && sprite_access) begin
            // If at the start of a new 8x8 pixel line load new data, else shift circular
            sprite_line <= {sprite_line[WIDTH - 2: 0], new_line ? sprite_data : sprite_line[WIDTH - 1]};
        end
    end

    // For the first line of a 8x8 pixels use the data directly from the sprite
    // For the lines afterwards reuse the data inside sprite_line
    assign sprite_pixel = new_line ? sprite_data : sprite_line[WIDTH - 1];

endmodule
