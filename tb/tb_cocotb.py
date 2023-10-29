# SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
# SPDX-License-Identifier: Apache-2.0

import os
import random
from pathlib import Path
from PIL import Image, ImageChops

import cocotb
from cocotb.clock import Clock
from cocotb.runner import get_runner
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.types import LogicArray

from cocotbext.spi import SpiBus, SpiConfig, SpiMaster

# Parameters
WIDTH    = 800;
HEIGHT   = 600;

HFRONT   = 40;
HSYNC    = 128;
HBACK    = 88;

VFRONT   = 1;
VSYNC    = 4;
VBACK    = 23;

CMD_SPRITE_DATA = 0x0
CMD_COLOR1      = 0x1
CMD_COLOR2      = 0x2
CMD_COLOR3      = 0x3
CMD_COLOR4      = 0x4
CMD_SPRITE_X    = 0x5
CMD_SPRITE_Y    = 0x6
CMD_MISC        = 0x7

# Global variables
COLOR1 = 0x31
COLOR2 = 0x15
COLOR3 = 0x0C
COLOR4 = 0x21

PIXEL_SIZE = 8

SPRITE_X = 0
SPRITE_Y = 0

SPRITE_HEIGHT = 12
SPRITE_WIDTH = 12

SPRITE_TT = [
    [0,0,0,1,1,1,1,1,1,0,0,0],
    [0,0,1,0,0,0,0,0,0,1,0,0],
    [0,1,1,1,1,1,1,0,0,0,1,0],
    [1,1,1,1,1,1,1,0,0,0,0,1],
    [0,0,0,1,1,0,0,0,0,0,0,1],
    [1,0,0,1,1,1,1,1,1,1,0,1],
    [1,0,0,1,1,1,1,1,1,1,0,1],
    [1,0,0,1,1,0,1,1,0,0,0,1],
    [1,0,0,1,1,0,1,1,0,0,0,1],
    [0,1,0,0,0,0,1,1,0,0,1,0],
    [0,0,1,0,0,0,1,1,0,1,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0],
]

SPRITE_DRINK = [
    [0,0,0,0,0,0,0,1,1,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,0],
    [1,1,1,1,0,1,0,1,1,1,1,0],
    [1,0,0,0,0,1,0,0,0,0,1,0],
    [0,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,0,0,1,1,1,0,0,0],
    [0,0,0,1,0,0,1,1,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0],
]

SPRITE_HEART = [
    [0,0,1,1,0,0,0,1,1,0,0,0],
    [0,1,1,1,1,0,1,1,1,1,0,0],
    [1,1,1,1,1,1,1,1,0,1,1,0],
    [1,1,1,1,1,1,1,1,1,0,1,0],
    [1,1,1,1,1,1,1,1,1,0,1,0],
    [1,1,1,1,1,1,1,1,0,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,0,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
]

SPRITE_SPIRAL = [
    [0,0,0,1,1,1,1,1,0,0,0,0],
    [0,1,1,0,0,0,0,0,1,1,0,0],
    [1,0,0,0,0,0,0,0,0,0,1,0],
    [1,0,0,0,0,0,0,0,0,0,1,0],
    [0,0,0,0,1,1,1,1,0,0,0,1],
    [0,0,0,1,0,0,0,0,1,0,0,1],
    [0,0,1,0,0,1,1,0,1,0,0,1],
    [0,0,1,0,1,0,0,0,1,0,0,1],
    [0,0,1,0,1,0,0,1,0,0,1,0],
    [0,0,1,0,0,1,1,0,0,0,1,0],
    [0,0,0,1,0,0,0,0,1,1,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0],
]

SPRITE = SPRITE_TT

ENABLE_SPRITE_BG = 0
BACKGROUND_SEL = 2

# Reset coroutine
async def reset_dut(rst_ni, duration_ns):
    rst_ni.value = 0
    await Timer(duration_ns, units="ns")
    rst_ni.value = 1
    rst_ni._log.debug("Reset complete")

# Draw the current frame and return it
async def draw_frame(dut):
    screen_x = -HBACK
    screen_y = -VBACK

    print(dut.timing_hor.counter.value.integer)
    print(dut.timing_ver.counter.value.integer)
    print(f"line {screen_y}")

    image = Image.new('RGB', (WIDTH, HEIGHT), "black")
    pixels = image.load()

    while (1):
        await RisingEdge(dut.clk)
    
        # Expand color data
        r = dut.rrggbb.value[0:1] << 6
        if (r & 1<<6):
            r = r | 0x3F
        g = dut.rrggbb.value[2:3] << 6
        if (g & 1<<6):
            g = g | 0x3F
        b = dut.rrggbb.value[4:5] << 6
        if (b & 1<<6):
            b = b | 0x3F

        # Inside drawing area
        if screen_y >= 0 and screen_y < HEIGHT and screen_x >= 0 and screen_x < WIDTH:
            #print(dut.timing_hor.counter.value.integer)
            #print(dut.timing_ver.counter.value.integer)
            pixels[screen_x, screen_y] = (r, g, b)
        
        # Received hsync
        if (dut.hsync.value == 1):
            await FallingEdge(dut.hsync)
            screen_y += 1
            print(dut.timing_hor.counter.value.integer)
            print(dut.timing_ver.counter.value.integer)
            print(f"line {screen_y}")
            screen_x = -HBACK

        # Received vsync
        elif (dut.vsync.value == 1):
            await FallingEdge(dut.vsync)
            await FallingEdge(dut.hsync)
            return image
        else:
            screen_x += 1

def sprite2bytes(sprite):
    bits = ""
    
    for row in sprite:
        for bit in row:
            bits += str(bit)
    
    byte_data = [int(bits[x:x+8], 2) for x in range(0, len(bits), 8)]
    
    return byte_data

def hex2rgb(color):
    r = (color & 0x30) << 2 
    if (r & 1<<6):
        r = r | 0x3F
    g = (color & 0xC) << 4
    if (g & 1<<6):
        g = g | 0x3F
    b = (color & 0x3) << 6
    if (b & 1<<6):
        b = b | 0x3F

    return (r, g, b)

def draw_frame_software():
    if BACKGROUND_SEL != 0:
        print("Error: Only BACKGROUND_SEL=0 supported")
    
    sprite = Image.new('RGBA', (SPRITE_WIDTH, SPRITE_HEIGHT), (0, 0, 0, 0))
    pixels = sprite.load()
    
    for y in range(SPRITE_HEIGHT):
        for x in range(SPRITE_WIDTH):
            if SPRITE[y][x]:
                pixels[x, y] = hex2rgb(COLOR1)
            elif ENABLE_SPRITE_BG:
                pixels[x, y] = hex2rgb(COLOR2)

    big_sprite = sprite.resize((SPRITE_WIDTH*PIXEL_SIZE, SPRITE_HEIGHT*PIXEL_SIZE), Image.NEAREST)

    image = Image.new('RGB', (WIDTH, HEIGHT), hex2rgb(COLOR3))
    pixels = image.load()
    
    image.paste(big_sprite, (SPRITE_X*PIXEL_SIZE, SPRITE_Y*PIXEL_SIZE), big_sprite)
    
    return image

# Send cmd and payload over SPI
async def spi_send_cmd(dut, spi_master, cmd, data, burst=False):
    print(f'CMD: {cmd} DATA: {data}')
    await spi_master.write(cmd)
    await spi_master.write(data, burst=burst)

@cocotb.test()
async def simple_test(dut):
    """This test sends commands to the design via SPI and
       compares the resulting frame with a software rendering"""

    global SPRITE
    
    global SPRITE_X
    global SPRITE_Y
    
    global COLOR1
    global COLOR2
    global COLOR3
    global COLOR4
    
    global BACKGROUND_SEL
    global ENABLE_SPRITE_BG

    # Start the clock
    c = Clock(dut.clk, 10, 'ns')
    await cocotb.start(c.start())

    spi_bus = SpiBus.from_prefix(dut, "spi")

    spi_config = SpiConfig(
        word_width = 8,
        sclk_freq  = 2e6,
        cpol       = False,
        cpha       = True,
        msb_first  = True,
        frame_spacing_ns = 500
    )

    spi_master = SpiMaster(spi_bus, spi_config)

    # Execution will block until reset_dut has completed
    await reset_dut(dut.reset_n, 50)
    dut._log.info("Reset done")
    
    await FallingEdge(dut.vsync)
    await FallingEdge(dut.hsync)
    
    # Start thread to draw frame
    taks_draw_frame = await cocotb.start(draw_frame(dut))
    
    # SPI commands
    SPRITE_X = 0x10
    SPRITE_Y = 0x10
    BACKGROUND_SEL = 0
    ENABLE_SPRITE_BG = 0
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config1 done")

    image = await taks_draw_frame.join()
    gold = draw_frame_software()

    image.save(f"test1.png")
    gold.save(f"gold1.png")

    # Check that images are the same
    diff = ImageChops.difference(image.convert('RGB'), gold.convert('RGB'))
    assert(not diff.getbbox())

@cocotb.test()
async def create_images(dut):
    """This test creates multiple images
       of all four backgrounds"""

    global SPRITE
    
    global SPRITE_X
    global SPRITE_Y
    
    global COLOR1
    global COLOR2
    global COLOR3
    global COLOR4
    
    global BACKGROUND_SEL
    global ENABLE_SPRITE_BG

    # Start the clock
    c = Clock(dut.clk, 10, 'ns')
    await cocotb.start(c.start())

    spi_bus = SpiBus.from_prefix(dut, "spi")

    spi_config = SpiConfig(
        word_width = 8,
        sclk_freq  = 2e6,
        cpol       = False,
        cpha       = True,
        msb_first  = True,
        frame_spacing_ns = 500
    )

    spi_master = SpiMaster(spi_bus, spi_config)

    # Execution will block until reset_dut has completed
    await reset_dut(dut.reset_n, 50)
    dut._log.info("Reset done")
    
    await FallingEdge(dut.vsync)
    await FallingEdge(dut.hsync)
    
    # Start thread to draw frame
    taks_draw_frame = await cocotb.start(draw_frame(dut))
    
    # SPI commands
    SPRITE_X = 0x13
    SPRITE_Y = 0x13
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    BACKGROUND_SEL = 2
    ENABLE_SPRITE_BG = 0
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config1 done")

    image = await taks_draw_frame.join()
    image.save(f"image1.png")

    # Start thread to draw frame
    taks_draw_frame = await cocotb.start(draw_frame(dut))
    
    # SPI commands
    SPRITE_X = 44
    SPRITE_Y = 32
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    SPRITE = SPRITE_HEART
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], sprite2bytes(SPRITE), burst=True)
    COLOR1 = 0x30 # Red
    COLOR3 = 0x2A # Light Gray
    await spi_send_cmd(dut, spi_master, [CMD_COLOR1], [COLOR1])
    await spi_send_cmd(dut, spi_master, [CMD_COLOR3], [COLOR3])
    BACKGROUND_SEL = 0
    ENABLE_SPRITE_BG = 0
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config2 done")

    image = await taks_draw_frame.join()
    image.save(f"image2.png")

    # Start thread to draw frame
    taks_draw_frame = await cocotb.start(draw_frame(dut))
    
    # SPI commands
    SPRITE_X = 0x40
    SPRITE_Y = 0x20
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    SPRITE = SPRITE_DRINK
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], sprite2bytes(SPRITE), burst=True)
    COLOR1 = 0x1F
    COLOR3 = 0x30
    await spi_send_cmd(dut, spi_master, [CMD_COLOR1], [COLOR1])
    await spi_send_cmd(dut, spi_master, [CMD_COLOR3], [COLOR3])

    BACKGROUND_SEL = 1
    ENABLE_SPRITE_BG = 1
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config3 done")

    image = await taks_draw_frame.join()
    image.save(f"image3.png")
    
    # Start thread to draw frame
    taks_draw_frame = await cocotb.start(draw_frame(dut))
    
    # SPI commands
    SPRITE_X = 0x07
    SPRITE_Y = 0x07
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    SPRITE = SPRITE_SPIRAL
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], sprite2bytes(SPRITE), burst=True)
    COLOR1 = 0x33
    COLOR3 = 0x0A
    await spi_send_cmd(dut, spi_master, [CMD_COLOR1], [COLOR1])
    await spi_send_cmd(dut, spi_master, [CMD_COLOR3], [COLOR3])

    BACKGROUND_SEL = 3
    ENABLE_SPRITE_BG = 1
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config4 done")

    image = await taks_draw_frame.join()
    image.save(f"image4.png")
    
    
@cocotb.test()
async def draw_multiple_sprites(dut):
    """This test draws multiple identical
       sprites in one frame"""

    global SPRITE
    
    global SPRITE_X
    global SPRITE_Y
    
    global COLOR1
    global COLOR2
    global COLOR3
    global COLOR4
    
    global BACKGROUND_SEL
    global ENABLE_SPRITE_BG

    # Start the clock
    c = Clock(dut.clk, 10, 'ns')
    await cocotb.start(c.start())

    spi_bus = SpiBus.from_prefix(dut, "spi")

    spi_config = SpiConfig(
        word_width = 8,
        sclk_freq  = 2e6,
        cpol       = False,
        cpha       = True,
        msb_first  = True,
        frame_spacing_ns = 500
    )

    spi_master = SpiMaster(spi_bus, spi_config)

    # Execution will block until reset_dut has completed
    await reset_dut(dut.reset_n, 50)
    dut._log.info("Reset done")
    
    await FallingEdge(dut.vsync)
    await FallingEdge(dut.hsync)
    
    # Start thread to draw frame
    taks_draw_frame = await cocotb.start(draw_frame(dut))
    
    # SPI commands
    SPRITE_X = 1+2
    SPRITE_Y = 1+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    ENABLE_SPRITE_BG = 1
    BACKGROUND_SEL = 2
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])
    
    for i in range (23):
        await FallingEdge(dut.hsync)
    
    dut._log.info("Start line")
    
    for i in range (15*8):
        await FallingEdge(dut.hsync)

    # SPI commands
    SPRITE_X = 16+2+5
    SPRITE_Y = 16+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    BACKGROUND_SEL = 3
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config done")

    for i in range (15*8):
        await FallingEdge(dut.hsync)

    # SPI commands
    SPRITE_X = 31+2+5+6
    SPRITE_Y = 31+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    BACKGROUND_SEL = 1
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config done")
    
    for i in range (15*8):
        await FallingEdge(dut.hsync)
    
    # SPI commands
    SPRITE_X = 46+2+5+6+5
    SPRITE_Y = 46+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    BACKGROUND_SEL = 3
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config done")

    for i in range (15*8):
        await FallingEdge(dut.hsync)

    # SPI commands
    SPRITE_X = 61+2+22
    SPRITE_Y = 61+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    BACKGROUND_SEL = 2
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])

    dut._log.info("Config done")

    image = await taks_draw_frame.join()
    image.save(f"identical_sprites.png")

@cocotb.test()
async def draw_different_sprites(dut):
    """This test draws multiple different
       sprites in one frame"""

    global SPRITE
    
    global SPRITE_X
    global SPRITE_Y
    
    global COLOR1
    global COLOR2
    global COLOR3
    global COLOR4
    
    global BACKGROUND_SEL
    global ENABLE_SPRITE_BG

    # Start the clock
    c = Clock(dut.clk, 10, 'ns')
    await cocotb.start(c.start())

    spi_bus = SpiBus.from_prefix(dut, "spi")

    spi_config = SpiConfig(
        word_width = 8,
        sclk_freq  = 2e6,
        cpol       = False,
        cpha       = True,
        msb_first  = True,
        frame_spacing_ns = 500
    )

    spi_master = SpiMaster(spi_bus, spi_config)

    # Execution will block until reset_dut has completed
    await reset_dut(dut.reset_n, 50)
    dut._log.info("Reset done")
    
    await FallingEdge(dut.vsync)
    await FallingEdge(dut.hsync)
    
    # Start thread to draw frame
    taks_draw_frame = await cocotb.start(draw_frame(dut))
    
    # SPI commands
    SPRITE_X = 1+2
    SPRITE_Y = 1+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
    ENABLE_SPRITE_BG = 0
    BACKGROUND_SEL = 0
    await spi_send_cmd(dut, spi_master, [CMD_MISC], [ENABLE_SPRITE_BG << 3 | BACKGROUND_SEL])
    
    for i in range (23):
        await FallingEdge(dut.hsync)
    
    dut._log.info("Start line")
    
    for i in range (15*8):
        await FallingEdge(dut.hsync)

    SPRITE = SPRITE_SPIRAL
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], sprite2bytes(SPRITE), burst=True)

    for i in range (15*8):
        await FallingEdge(dut.hsync)

    # SPI commands
    SPRITE_X = 31+2+5+6
    SPRITE_Y = 31+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])
 
    dut._log.info("Config done")
    
    for i in range (15*8):
        await FallingEdge(dut.hsync)

    SPRITE = SPRITE_DRINK
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], sprite2bytes(SPRITE), burst=True)

    for i in range (15*8):
        await FallingEdge(dut.hsync)

    # SPI commands
    SPRITE_X = 61+2+22
    SPRITE_Y = 61+2
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [SPRITE_X])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [SPRITE_Y])

    dut._log.info("Config done")

    image = await taks_draw_frame.join()
    image.save(f"different_sprites.png")

def test_runner():
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus") # "verilator" "icarus"

    proj_path = Path(__file__).resolve().parent

    verilog_sources = [proj_path / "../src/top.sv",
                        proj_path / "../src/sprite_access.sv",
                        proj_path / "../src/sprite_data.sv",
                        proj_path / "../src/sprite_movement.sv",
                        proj_path / "../src/background.sv",
                        proj_path / "../src/timing.sv",
                        proj_path / "../src/synchronizer.sv",
                        proj_path / "../src/spi_receiver.sv"]

    runner = get_runner(sim)
    runner.build(
        verilog_sources=verilog_sources,
        defines=[("COCOTB", 1)],
        build_args=[],#["--trace-fst", "--trace-structs"],
        hdl_toplevel="top",
        always=True,
    )

    runner.test(hdl_toplevel="top", test_module="tb_cocotb,")


if __name__ == "__main__":
    test_runner()
