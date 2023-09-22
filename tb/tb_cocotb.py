# SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import random
from pathlib import Path
from PIL import Image

import cocotb
from cocotb.clock import Clock
from cocotb.runner import get_runner
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.types import LogicArray

from cocotbext.spi import SpiSignals, SpiConfig, SpiMaster

# Parameters
WIDTH    = 800;
HEIGHT   = 600;

HFRONT   = 40;
HSYNC    = 128;
HBACK    = 88;

VFRONT   = 1;
VSYNC    = 4;
VBACK    = 23;

# Global variables

screen_x = -HBACK -1
screen_y = -VBACK
frame = 0

MyImg = Image.new( 'RGB', (WIDTH, HEIGHT), "black")
pixels = MyImg.load()

# Reset coroutine
async def reset_dut(rst_ni, duration_ns):
    rst_ni.value = 0
    await Timer(duration_ns, units="ns")
    rst_ni.value = 1
    rst_ni._log.debug("Reset complete")

# Draw the frame
async def inc_h(dut):
    global screen_x
    global screen_y
    global frame
    global pixels
    while (1):
        await RisingEdge(dut.clk)
        screen_x += 1
        
        r = dut.rrggbb.value[0:1] << 6
        g = dut.rrggbb.value[2:3] << 6
        b = dut.rrggbb.value[4:5] << 6
        
        # Inside drawing area
        if screen_y >= 0 and screen_y < HEIGHT and screen_x >= 0 and screen_x < WIDTH:
            pixels[screen_x, screen_y] = (r, g, b)
        
        # Received hsync
        if (dut.hsync.value == 1):
            await FallingEdge(dut.hsync)
            print(f"line {screen_y}")
            screen_x = -HBACK-1
            screen_y += 1
        
        # Received vsync
        if (dut.vsync.value == 1):
            print("frame!")
            MyImg.save(f"frame{frame}.png")
            await FallingEdge(dut.vsync)
            frame += 1
            screen_y = -VBACK-1

# Send cmd and payload over SPI
async def spi_send_cmd(dut, spi_master, cmd, data):
    print(f'CMD: {cmd} DATA: {data}')
    spi_master.write_nowait(cmd)
    await spi_master.wait()
    await spi_master.read()

    spi_master.write_nowait(data)
    await spi_master.wait()
    read_bytes = await spi_master.read()
    
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    await RisingEdge(dut.clk)

    return read_bytes

@cocotb.test()
async def simple_test(dut):
    """This test sends commands to the design via
       SPI and draws two frames"""

    dut._log.debug("Start")
    print("start")

    # Start the clock
    c = Clock(dut.clk, 10, 'ns')
    await cocotb.start(c.start())
    
    spi_signals = SpiSignals(
        sclk = dut.spi_sclk,     # required
        mosi = dut.spi_mosi,     # required
        miso = dut.spi_miso,     # required
        cs   = dut.spi_cs,       # required
        cs_active_low = True     # optional (assumed True)
    )
    
    spi_config = SpiConfig(
        word_width = 8,
        sclk_freq  = 1e6,
        cpol       = False,
        cpha       = True,
        msb_first  = True,
    )

    spi_master = SpiMaster(spi_signals, spi_config)

    # Execution will block until reset_dut has completed
    await reset_dut(dut.reset_n, 50)
    dut._log.debug("Reset done")
    
    # Start thread to draw frame
    await cocotb.start(inc_h(dut))
    
    CMD_SPRITE_DATA = 0x0
    CMD_COLOR1      = 0x1
    CMD_COLOR2      = 0x2
    CMD_COLOR3      = 0x3
    CMD_COLOR4      = 0x4
    CMD_SPRITE_X    = 0x5
    CMD_SPRITE_Y    = 0x6
    CMD_MISC        = 0x7
    
    # SPI commands
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [0x10])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [0x10])
    
    await spi_send_cmd(dut, spi_master, [CMD_COLOR1], [0x13])
    
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], [0xFF])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], [0xFF])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], [0xFF])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_DATA], [0xF0, 0xF0, 0xF0])

    # Wait for frame
    await RisingEdge(dut.vsync)
    await FallingEdge(dut.vsync)
    
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_X], [0x1f])
    await spi_send_cmd(dut, spi_master, [CMD_SPRITE_Y], [0x10])
    
    # Wait for frame
    await RisingEdge(dut.vsync)
    await FallingEdge(dut.vsync)

    await RisingEdge(dut.clk)

    print("done")

def test_runner():
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "verilator") # "verilator" "icarus"

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
        build_args=["--trace-fst", "--trace-structs"],
        hdl_toplevel="top",
        always=True,
    )

    runner.test(hdl_toplevel="top", test_module="tb_cocotb,")


if __name__ == "__main__":
    test_runner()
