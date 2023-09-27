![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg)

# One Sprite Pony

A one-trick pony is someone or something that is good at doing only one thing. Accordingly, a one-sprite pony can display only one sprite, and that's exactly what this design does:

![animation.gif](animation.gif)

This Verilog design produces SVGA 800x600 60Hz output with a background and one sprite. Internally, the resolution is reduced to 100x75, thus one pixel of the sprite is actually 8x8 pixels.

The sprite is 12x12 pixel in size and is initialized at startup with a pixelated version of the TinyTapeout logo.

This design targets 1 Tile of [TinyTapeout 5](https://tinytapeout.com).

The goal is pixel perfect rendering. To achieve this goal, I created regression tests in cocotb, that compare the output image to a software rendering.

## Capabilities

- SVGA 800x600 60Hz output with 2 bits per color (internally reduced to 100x75)
- 40 MHz or 10 MHz operation TODO
- Sprite with 12x12 pixels
	- foreground and background color
- 4 different colors
- 4 different backgrounds
	- Solid color
	- Funky
	- Diagonal stripes
	- Horizontal Stripes
- SPI Receiver
	- Set sprite data
	- Set colors (1-4)
	- Set background (4 types)
	- Set sprite x/y position

|   |   |
|---|---|
| ![image1.png](img/image1.png)  | ![image2.png](img/image2.png)  |
| ![image3.png](img/image3.png)  | ![image4.png](img/image4.png)  |

## SPI Register

Register Map

| Addr Hex | Name | Type | Reset Value | Description |
|----------|------|------|-------------|-------------|
| 0x00     | SPRITE_DATA | R/W | TinyTapeout Logo | Stores the data for the sprite, you can contionously read/write it by keeping CS asserted |
| 0x01     | COLOR1     | R/W     | TODO            | 6 bit color in format RRGGBB used as sprite foreground            |
| 0x02     | COLOR2     | R/W     | TODO            | 6 bit color in format RRGGBB used as sprite background            |
| 0x03     | COLOR3     | R/W     | TODO            | 6 bit color in format RRGGBB used as solid color background           |
| 0x04     | COLOR4     | R/W     | TODO            | 6 bit color in format RRGGBB            |
| 0x05     | SPRITE_X     | R/W     | TODO            | 6 bit x position of the sprite            |
| 0x06     | SPRITE_Y     | R/W     | TODO            | 6 bit y position of the sprite            |
| 0x07     | MISC     | R/W     | TODO            | Various Settings, see below            |

Details for MISC Register:

- Bits 1:0: Background selection
	- 00: Solid color
	- 01: Funky
	- 10: Diagonal Stripes
	- 11: Horizontal Stripes
	New background type is only assigned at hsync to prevent glitching
- Bit 2: Enable movement of the sprite
- Bit 3: Enable sprite background (transparency)
- Bit 4: Enable reduced frequency mode (10 MHz operation) TODO
- Bits 7:5: TODO

Attention when reading registers that provide less than 8 bits, e.g. all colors and x/y position. The last 2 bits read will be the first two bits shifted in. This means you need to shift the received data by >>2 before using it.

## Creating your own sprites

TODO

## Creating your own gif

TODO

## Verification

TODO

## Hardening

TODO

## Tips and Tricks

### Displaying multiple Sprites

Just because One Sprite Pony contains only sprite doesn't mean it can't display more than one.

By using scanline-tricks it is able to display the same sprite multiple times and change background types:

![identical_sprites.png](img/identical_sprites.png)

If you are fast enough, you can even swap the sprite in between:

![different_sprites.png](img/different_sprites.png)

Just write to the various registers while the frame is drawn.

I am excited what you are going to do with it!

## Different Applications?

With some imagination One Sprite Pony can become so much more:

1. ROM for TT Sprite (just read out the sprite data)

2. RAM (read and write sprite data and registers)

3. hand warmer? (the design has a density of 90%, but since all other designs are disabled at the same time, the chip will probably not warm up ;) )
