// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: GPL-3.0-or-later

`timescale 1ns/1ps

module sprite_movement #(
    parameter SPRITE_WIDTH,
    parameter SPRITE_HEIGHT,
    parameter WIDTH_SMALL,
    parameter HEIGHT_SMALL
)(
    input  logic clk,       // clock
    input  logic reset_n,   // reset 
    
    input  logic next_frame,
    
    output logic [7:0] sprite_x,
    output logic [7:0] sprite_y
);

    logic sprite_x_dir;
    logic sprite_y_dir;
    
    //logic wall_hit;
    //assign wall_hit = 
    
    /* verilator lint_off WIDTH */
    
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
                    
                    if (sprite_x == (WIDTH_SMALL - SPRITE_WIDTH - 1)) begin
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
                    
                    if (sprite_y == (HEIGHT_SMALL - SPRITE_HEIGHT - 1)) begin
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

endmodule
