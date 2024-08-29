'''
Created on Jan 9, 2024

Code here, in main.py, runs on every power-up.

You can put anything you like in here, including any utility functions 
you might want to have access to when connecting to the REPL.  

If you want to use the SDK, all
you really need is something like
  
      tt = DemoBoard()

Then you can 
    # enable test project
    tt.shuttle.tt_um_test.enable()

and play with i/o as desired.

This code accesses the PowerOnSelfTest functions to:

    * check if the project clock button was held during powerup;
    * if so, run a basic test of the bidir pins (and implicitly of 
      the mux, output reads etc); and
    * and check if this was a first boot, to run special codes in
      such cases


@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import sys
import math
import ttboard.util.time as time
from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard, Pins
from ttboard.boot.post import PowerOnSelfTest

from machine import Pin
from machine import SoftSPI

from pio_spi import PIOSPI

tt = None
def startup():
    
    # construct DemoBoard
    # either pass an appropriate RPMode, e.g. RPMode.ASIC_RP_CONTROL
    # or have "mode = ASIC_RP_CONTROL" in ini DEFAULT section
    ttdemoboard = DemoBoard()

    
    print("\n\n")
    print("The 'tt' object is available.")
    print()
    print("Projects may be enabled with tt.shuttle.PROJECT_NAME.enable(), e.g.")
    print("tt.shuttle.tt_um_urish_simon.enable()")
    print()
    print("Pins may be accessed by name, e.g. tt.out3() to read or tt.in5(1) to write.")
    print("Config of pins may be done using mode attribute, e.g. ")
    print("tt.uio3.mode = Pins.OUT")
    print("\n\n")
    
    return ttdemoboard

def autoClockProject(freqHz:int):
    tt.clock_project_PWM(freqHz)
    
def stopClocking():
    tt.clock_project_stop()

def test_design_tnt_counter():
    # select the project from the shuttle
    tt.shuttle.tt_um_test.enable()
    
    #reset
    tt.reset_project(True)

    # enable the internal counter of test design
    tt.in0(1)

    # take out of reset
    tt.reset_project(False)
    
    print('Running tt_um_test, printing output...Ctrl-C to stop')
    time.sleep_ms(300)
    
    tt.clock_project_PWM(10)
    try:
        while True:
            print(hex(tt.output_byte & 0x0f)) # could do ...out0(), out1() etc
            time.sleep_ms(100)
    except KeyboardInterrupt:
        tt.clock_project_stop()
        
    

def test_neptune():
    tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
    for i in range(20, 340, 10):
        tt.in5.pwm(i)
        time.sleep_ms(1000)
        print(f'Input at {i}Hz, outputs are {hex(tt.output_byte)}')
    
    tt.in5.pwm(0) # disable pwm


# check if this is the first boot, if so, 
# handle that
if PowerOnSelfTest.first_boot():
    print('First boot!')
    PowerOnSelfTest.handle_first_boot()
    


# take a look at project user button state at startup
# all this "raw" pin access should happen before the DemoBoard object 
# is instantiated
run_post_tests = PowerOnSelfTest.dotest_buttons_held()
# or get a dict with PowerOnSelfTest.read_all_pins()


tt = startup()

# run a test if clock button held high 
# during startup
if run_post_tests:
    print('\n\nDoing startup test!')
    wait_count = 0
    while PowerOnSelfTest.dotest_buttons_held() and wait_count < 10:
        print("Waiting for button release...")
        time.sleep_ms(250)
        wait_count += 1
    
    post = PowerOnSelfTest(tt)
    if not post.test_bidirs():
        print('ERRORS encountered while running POST bidir test!')
    else:
        print('Startup test GOOD')
        tt.load_default_project()
    print('\n\n')

#tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
print(tt)
print()

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

# Parameters
WIDTH    = 800
HEIGHT   = 600

PIXEL_SIZE = 8

SPRITE_X = 0
SPRITE_Y = 0

SPRITE_HEIGHT = 12
SPRITE_WIDTH = 12

CMD_SPRITE_DATA = b'\x00'
CMD_COLOR1      = b'\x01'
CMD_COLOR2      = b'\x02'
CMD_COLOR3      = b'\x03'
CMD_COLOR4      = b'\x04'
CMD_SPRITE_X    = b'\x05'
CMD_SPRITE_Y    = b'\x06'
CMD_MISC        = b'\x07'

COLOR_BLACK = b'\x00'
COLOR_DARK_GRAY = b'\x15'
COLOR_GRAY = b'\x2A'
COLOR_WHITE = b'\x3F'

COLOR_BOLD_RED = b'\x30'
COLOR_RED = b'\x20'
COLOR_LIGHT_RED = b'\x10'

COLOR_BOLD_GREEN = b'\x0C'
COLOR_GREEN = b'\x08'
COLOR_LIGHT_GREEN = b'\x04'

COLOR_BOLD_BLUE = b'\x03'
COLOR_BLUE = b'\x02'
COLOR_LIGHT_BLUE = b'\x01'

COLOR_PINK = '\x31'
COLOR_DARK_PINK = '\x21'

colors = [
    COLOR_BLACK,
    COLOR_DARK_GRAY,
    COLOR_GRAY,
    COLOR_WHITE,

    COLOR_BOLD_RED,
    COLOR_RED,
    COLOR_LIGHT_RED,
    COLOR_WHITE,

    COLOR_BOLD_GREEN,
    COLOR_GREEN,
    COLOR_LIGHT_GREEN,
    COLOR_WHITE,

    COLOR_BOLD_BLUE,
    COLOR_BLUE,
    COLOR_LIGHT_BLUE,
    COLOR_WHITE
]

COLOR1 = '\x31'
COLOR2 = '\x15'
COLOR3 = '\x0C'
COLOR4 = '\x2C'

frame_trig = False
def isr_frame(t):
    global frame_trig
    frame_trig = True

line_trig = False
def isr_line(t):
    global line_trig
    line_trig = True

def sync_frame():
    global frame_trig
    frame_trig = False
    while not frame_trig:
        pass

def sync_line():
    global line_trig
    line_trig = False
    while not line_trig:
        pass

def sync():
    sync_frame()

    for i in range(4):
        sync_line()

def sprite2bytes(sprite):
    bytes = []
    
    bitstring = ''
    for row in sprite:
        for bit in row:
            bitstring += str(bit)

    return int(bitstring, 2).to_bytes(len(bitstring) // 8, 'big')

def send_cmd(spi, cmd, data):
    tt.uio0(0) # start
    spi.write(cmd)
    spi.write(data)
    tt.uio0(1) # stop


def brute():
    tt.shuttle.tt_um_top_mole99.enable()
    
    # Set freq to 40MHz
    tt.clock_project_PWM(40e6)
    
    # CS - chip select, active low
    tt.uio0.mode = Pins.OUT
    tt.uio0(0)
    
    #spi = SoftSPI(baudrate=int(20e6), polarity=0, phase=1, bits=8, sck=tt.pin_uio3, mosi=tt.pin_uio1, miso=tt.pin_uio2) #firstbit=MSB
    spi = PIOSPI(sm_id=0, pin_mosi=tt.pin_uio1, pin_miso=tt.pin_uio2, pin_sck=tt.pin_uio3, cpha=True, cpol=False, freq=int(20e6))

    tt.pin_cinc_out3.irq(trigger=Pin.IRQ_FALLING, handler=isr_frame) # vsync
    tt.pin_out7.irq(trigger=Pin.IRQ_FALLING, handler=isr_line) # hsync
    
    time.sleep_ms(7000)
    
    print('Ready?')
    
    for i in 5*[4, 11]:#range(0, 800):
        sys.stdin.readline()

        print('i = ' + str(i))

        tt.reset_project(True)
        tt.reset_project(False)
        
        time.sleep_ms(7000)
        
        # Solid color background, stop movement
        send_cmd(spi, CMD_MISC, (0b0000000).to_bytes(1, 'little'))
        
        # Loops
        MARGIN = 10

        for degree in range(0, 360, 4):
            x = MARGIN + int((math.cos(math.radians(degree))+1) * (WIDTH//PIXEL_SIZE-SPRITE_WIDTH-MARGIN*2)//2)
            y = MARGIN + int((math.sin(math.radians(degree))+1) * (HEIGHT//PIXEL_SIZE-SPRITE_HEIGHT-MARGIN*2)//2)
            
            sync_frame()
            for _ in range(i):
                sync_line()

            # Move sprite
            send_cmd(spi, CMD_SPRITE_X, x.to_bytes(1, 'little'))
            send_cmd(spi, CMD_SPRITE_Y, y.to_bytes(1, 'little'))

def pin_test():

    tt.uio0.mode = Pins.OUT
    tt.uio1.mode = Pins.OUT

    while 1:
        time.sleep_ms(1000)
        tt.uio0(1)
        tt.uio1(1)
        time.sleep_ms(1000)
        tt.uio0(0)
        tt.uio1(0)

def demo():
    tt.shuttle.tt_um_top_mole99.enable()

    # Set freq to 40MHz
    tt.clock_project_PWM(40e6)
    
    # CS - chip select, active low
    tt.uio0.mode = Pins.OUT
    tt.uio0(1)
    
    #spi = SoftSPI(baudrate=int(20e6), polarity=0, phase=1, bits=8, sck=tt.pin_uio3, mosi=tt.pin_uio1, miso=tt.pin_uio2) #firstbit=MSB
    spi = PIOSPI(sm_id=0, pin_mosi=tt.pin_uio1, pin_miso=tt.pin_uio2, pin_sck=tt.pin_uio3, cpha=True, cpol=False, freq=int(2e6)) # freq=int(126000000//10))

    tt.pin_cinc_out3.irq(trigger=Pin.IRQ_FALLING, handler=isr_frame) # vsync
    tt.pin_out7.irq(trigger=Pin.IRQ_FALLING, handler=isr_line) # hsync

    #tt.pin_uio4.irq(trigger=Pin.IRQ_FALLING, handler=isr_line) # next_line
    #tt.pin_uio5.irq(trigger=Pin.IRQ_FALLING, handler=isr_frame) # next_frame

    #sync()
        
    """# Reduced frequency mode 10MHz
    send_cmd(spi, CMD_MISC, (0b0011011).to_bytes(1, 'little'))
    tt.clock_project_PWM(10e6)
    time.sleep_ms(5000)"""
    
    print('Start:')
    sys.stdin.readline()

    sync()
    
    # Solid color background
    send_cmd(spi, CMD_MISC, (0b0000100).to_bytes(1, 'little'))
    sys.stdin.readline()
    
    # Funky background
    send_cmd(spi, CMD_MISC, (0b0000101).to_bytes(1, 'little'))
    sys.stdin.readline()
    
    # Diagonal background
    send_cmd(spi, CMD_MISC, (0b0000110).to_bytes(1, 'little'))
    sys.stdin.readline()
    
    # Horizontal background
    send_cmd(spi, CMD_MISC, (0b0000111).to_bytes(1, 'little'))
    sys.stdin.readline()

    # Test colors
    for index in range(len(colors)//4):
        color = colors[index*4:index*4+4]
    
        send_cmd(spi, CMD_COLOR1, color[0])
        send_cmd(spi, CMD_COLOR2, color[1])
        send_cmd(spi, CMD_COLOR3, color[2])
        send_cmd(spi, CMD_COLOR4, color[3])
        
        #time.sleep_ms(500)
        sys.stdin.readline()
        
    # Set default colors
    send_cmd(spi, CMD_COLOR1, COLOR1)
    send_cmd(spi, CMD_COLOR2, COLOR2)
    send_cmd(spi, CMD_COLOR3, COLOR3)
    send_cmd(spi, CMD_COLOR4, COLOR4)
    
    sys.stdin.readline()

    # Solid color background, stop movement
    send_cmd(spi, CMD_MISC, (0b0000000).to_bytes(1, 'little'))

    
    print('Set sprites:')
    sys.stdin.readline()
    
    while 1:
        sync_frame()
        send_cmd(spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_DRINK))    
        input = sys.stdin.readline()
        if input == '\n':
            break
    
    while 1:
        sync_frame()
        send_cmd(spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_SPIRAL))    
        input = sys.stdin.readline()
        if input == '\n':
            break
    
    while 1:
        sync_frame()
        send_cmd(spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_HEART))    
        input = sys.stdin.readline()
        if input == '\n':
            break    
    
    # Loops
    MARGIN = 12
    ROUNDS = 8
    for i in range(ROUNDS):

        for degree in range(0, 360, i+2):
            
            factor = 0.25 + 0.75 * (i/ROUNDS + (degree/360 * 1/ROUNDS))

            x = (WIDTH//PIXEL_SIZE-SPRITE_WIDTH)//2 + int(math.cos(math.radians(degree)) * (WIDTH//PIXEL_SIZE-SPRITE_WIDTH//2-MARGIN)//2 * factor)
            y = (HEIGHT//PIXEL_SIZE-SPRITE_HEIGHT)//2 + int(math.sin(math.radians(degree)) * (HEIGHT//PIXEL_SIZE-SPRITE_WIDTH//2-MARGIN)//2 * factor)
            
            sync_frame()
            #sync_line()
            #sync()

            # Move sprite
            send_cmd(spi, CMD_SPRITE_X, x.to_bytes(1, 'little'))
            send_cmd(spi, CMD_SPRITE_Y, y.to_bytes(1, 'little'))
    
    for i in range(ROUNDS-1, 0-1, -1):
        for degree in range(0, 360, i+2):
            factor = 0.25 + 0.75 * (i/ROUNDS + ((360-degree)/360 * 1/ROUNDS))

            x = (WIDTH//PIXEL_SIZE-SPRITE_WIDTH)//2 + int(math.cos(math.radians(degree)) * (WIDTH//PIXEL_SIZE-SPRITE_WIDTH//2-MARGIN)//2 * factor)
            y = (HEIGHT//PIXEL_SIZE-SPRITE_HEIGHT)//2 + int(math.sin(math.radians(degree)) * (HEIGHT//PIXEL_SIZE-SPRITE_WIDTH//2-MARGIN)//2 * factor)
            
            sync_frame()
            #sync_line()
            #sync()

            # Move sprite
            send_cmd(spi, CMD_SPRITE_X, x.to_bytes(1, 'little'))
            send_cmd(spi, CMD_SPRITE_Y, y.to_bytes(1, 'little'))
    
    while 1:
        sync_frame()
        send_cmd(spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_HEART))    
        input = sys.stdin.readline()
        if input == '\n':
            break
    
    # Diagonal background
    send_cmd(spi, CMD_MISC, (0b0000010).to_bytes(1, 'little'))
    sys.stdin.readline()
    
    # Reduced frequency 10MHz
    send_cmd(spi, CMD_MISC, (0b0010010).to_bytes(1, 'little'))
    tt.clock_project_PWM(10e6)
    
    sys.stdin.readline()

def test_one_sprite_pony():
    tt.shuttle.tt_um_top_mole99.enable()
    
    # Set freq to 40MHz
    tt.clock_project_PWM(40e6)
    
    # CS - chip select, active low
    tt.uio0.mode = Pins.OUT
    tt.uio0(1)
    
    spi = SoftSPI(baudrate=int(20e6), polarity=0, phase=1, bits=8, sck=tt.pin_uio3, mosi=tt.pin_uio1, miso=tt.pin_uio2) #firstbit=MSB

    tt.pin_uio4.irq(trigger=Pin.IRQ_FALLING, handler=isr_line)
    tt.pin_uio5.irq(trigger=Pin.IRQ_FALLING, handler=isr_frame)

    #sync()
        
    # Reduced frequency mode 10MHz
    send_cmd(spi, CMD_MISC, (0b0011011).to_bytes(1, 'little'))
    tt.clock_project_PWM(10e6)
    time.sleep_ms(5000)
    
    print('Start:')
    sys.stdin.readline()

    sync()

    # Set COLOR1
    send_cmd(spi, CMD_COLOR1, COLOR_WHITE)
    send_cmd(spi, CMD_COLOR2, COLOR_RED)
    send_cmd(spi, CMD_COLOR3, COLOR_GREEN)
    send_cmd(spi, CMD_COLOR4, COLOR_BLUE)
    
    time.sleep_ms(5000)
    
    sync()

    # Background 0
    send_cmd(spi, CMD_MISC, (0b0011000).to_bytes(1, 'little'))
    time.sleep_ms(1000)
    sync()
    # Background 1
    send_cmd(spi, CMD_MISC, (0b0011001).to_bytes(1, 'little'))
    time.sleep_ms(1000)
    sync()
    # Background 2
    send_cmd(spi, CMD_MISC, (0b0011001).to_bytes(1, 'little'))
    time.sleep_ms(1000)
    sync()
    # Background 3
    send_cmd(spi, CMD_MISC, (0b0011011).to_bytes(1, 'little'))
    time.sleep_ms(1000)

    MARGIN = 4
    for i in range(2):

        for degree in range(360):
            x = MARGIN + int((math.cos(math.radians(degree))+1) * (WIDTH//PIXEL_SIZE-SPRITE_WIDTH-MARGIN*2)//2)
            y = MARGIN + int((math.sin(math.radians(degree))+1) * (HEIGHT//PIXEL_SIZE-SPRITE_HEIGHT-MARGIN*2)//2)
            
            sync()

            # Move sprite
            send_cmd(spi, CMD_SPRITE_X, x.to_bytes(1, 'little'))
            send_cmd(spi, CMD_SPRITE_Y, y.to_bytes(1, 'little'))
    
    print('Multiple sprite:')
    sys.stdin.readline()

    MARGIN = 4
    for i in range(2):

        for degree in range(360):
            for index in range(2):
        
                x = MARGIN + int((math.cos(math.radians(degree + index*180))+1) * (WIDTH//PIXEL_SIZE-SPRITE_WIDTH-MARGIN*2)//2)
                y = MARGIN + int((math.sin(math.radians(degree + index*180))+1) * (HEIGHT//PIXEL_SIZE-SPRITE_HEIGHT-MARGIN*2)//2)
                
                sync()

                # Move sprite
                send_cmd(spi, CMD_SPRITE_X, x.to_bytes(1, 'little'))
                send_cmd(spi, CMD_SPRITE_Y, y.to_bytes(1, 'little'))
    
    print('Dual sprite:')
    sys.stdin.readline()
    
    for i in range(60*5):
        sync_frame()
        for i in range(5):
            sync_line()
        
        send_cmd(spi, CMD_SPRITE_Y, (0).to_bytes(1, 'little'))
        
        for i in range (30):
            sync_line()
        
        send_cmd(spi, CMD_SPRITE_Y, (32).to_bytes(1, 'little'))
    
    print('Set sprite:')
    sys.stdin.readline()
    
    sync()
    
    # Set sprite
    send_cmd(spi, CMD_SPRITE_DATA, b'\xFF\x00\xFF\x00\xFF\x00\xFF\x00\xFF\x00\xFF\x00\xFF\x00\xFF\x00\xFF\x00')
    
    print('Set sprite drink:')
    sys.stdin.readline()
    
    sync()
    
    send_cmd(spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_DRINK))
    
    print('Reduced frequency:')
    sys.stdin.readline()
    
    sync()
    
    # Reduced frequency mode 10MHz
    send_cmd(spi, CMD_MISC, (0b0011011).to_bytes(1, 'little'))
    tt.clock_project_PWM(10e6)
    time.sleep_ms(1000)
    
    print('Stop:')
    sys.stdin.readline()
