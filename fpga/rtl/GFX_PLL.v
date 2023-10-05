// SPDX-FileCopyrightText: © 2020 Bruno Levy <https://github.com/BrunoLevy/learn-fpga>
// SPDX-License-Identifier: BSD-3-Clause

// Define one of:
// MODE_640x480, MODE_800x600, MODE_1024x768, MODE_1280x1024.
// ("physical mode" sent to the HDMI)



module GFX_PLL(
    input  wire pclk,         // the board's clock
    output wire pixel_clk,    // pixel clock
    output wire pixel_clk_x5  // 5 times pixel clock freq (used by TMDS serializer)
	                      // The TMDS serializers operate at (pixel_clock_freq * 10), 
	                      // but we use DDR mode, hence (pixel_clock_freq * 5).
);

 // The parameters of the PLL, 
 // They are found by using: ecppll -i 25 -o <5*pixel_clock> -f foobar.v
   
 `ifdef MODE_640x480
   localparam CLKI_DIV = 1;
   localparam CLKOP_DIV = 5;
   localparam CLKOP_CPHASE = 2;
   localparam CLKOP_FPHASE = 0;
   localparam CLKFB_DIV = 5;
 `endif

 `ifdef MODE_800x600
   localparam CLKI_DIV = 1;
   localparam CLKOP_DIV = 3;
   localparam CLKOP_CPHASE = 1;
   localparam CLKOP_FPHASE = 0;
   localparam CLKFB_DIV = 8;
 `endif
   
 `ifdef MODE_1024x768
   localparam CLKI_DIV = 1;
   localparam CLKOP_DIV = 2;
   localparam CLKOP_CPHASE = 1;
   localparam CLKOP_FPHASE = 0;
   localparam CLKFB_DIV = 13;
 `endif

 `ifdef MODE_1280x1024
   localparam CLKI_DIV = 3;
   localparam CLKOP_DIV = 1;
   localparam CLKOP_CPHASE = 0;
   localparam CLKOP_FPHASE = 0;
   localparam CLKFB_DIV = 65;
 `endif

   // The PLL converts a 25 MHz clock into a (pixel_clock_freq * 5) clock
   // The (half) TMDS serializer clock is generated on pin CLKOP. 
   // In addition, the pixel clock (at TMDS freq/5) is generated on 
   // pin CLKOS (hence CLKOS_DIV = 5*CLKOP_DIV).
   (* ICP_CURRENT="12" *) (* LPF_RESISTOR="8" *) (* MFG_ENABLE_FILTEROPAMP="1" *) (* MFG_GMCREF_SEL="2" *)
   EHXPLLL #(
        .CLKI_DIV(CLKI_DIV),
        .CLKOP_DIV(CLKOP_DIV),
        .CLKOP_CPHASE(CLKOP_CPHASE),
        .CLKOP_FPHASE(CLKOP_FPHASE),
	.CLKOS_ENABLE("ENABLED"),
	.CLKOS_DIV(5*CLKOP_DIV),
	.CLKOS_CPHASE(CLKOP_CPHASE),
	.CLKOS_FPHASE(CLKOP_FPHASE),
        .CLKFB_DIV(CLKFB_DIV)
   ) pll_i (
        .CLKI(pclk),
        .CLKOP(pixel_clk_x5),
        .CLKFB(pixel_clk_x5),
	.CLKOS(pixel_clk),
        .PHASESEL0(1'b0),
        .PHASESEL1(1'b0),
        .PHASEDIR(1'b1),
        .PHASESTEP(1'b1),
        .PHASELOADREG(1'b1),
        .PLLWAKESYNC(1'b0),
        .ENCLKOP(1'b0)
   );

endmodule

