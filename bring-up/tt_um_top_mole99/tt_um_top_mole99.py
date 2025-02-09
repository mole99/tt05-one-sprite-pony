import sys
from machine import Pin
from machine import SoftSPI
from .pio_spi import PIOSPI
from ttboard.demoboard import DemoBoard, Pins

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

def send_cmd(tt, spi, cmd, data):
    tt.uio_in[0] = 0 # start
    spi.write(cmd)
    spi.write(data)
    tt.uio_in[0] = 1 # stop

def load_project(tt:DemoBoard):
    
    if not tt.shuttle.has('tt_um_top_mole99'):
        print("No tt_um_top_mole99 available in shuttle?")
        return False
    
    tt.shuttle.tt_um_top_mole99.enable()
    return True

def choose_color():
    print('Please choose color:')
    print("""0 - COLOR_BLACK
1 - COLOR_DARK_GRAY
2 - COLOR_GRAY
3 - COLOR_WHITE

4 - COLOR_BOLD_RED
5 - COLOR_RED
6 - COLOR_LIGHT_RED

7 - COLOR_BOLD_GREEN
8 - COLOR_GREEN
9 - COLOR_LIGHT_GREEN

10 - COLOR_BOLD_BLUE
11 - COLOR_BLUE
12 - COLOR_LIGHT_BLUE

13 - COLOR_PINK
14 - COLOR_DARK_PINK""")

    color = sys.stdin.readline().rstrip()

    if color == '0':
        return COLOR_BLACK
    elif color == '1':
        return COLOR_DARK_GRAY
    elif color == '2':
        return COLOR_GRAY
    elif color == '3':
        return COLOR_WHITE
    elif color == '4':
        return COLOR_BOLD_RED
    elif color == '5':
        return COLOR_RED
    elif color == '6':
        return COLOR_LIGHT_RED
    elif color == '7':
        return COLOR_BOLD_GREEN
    elif color == '8':
        return COLOR_GREEN
    elif color == '9':
        return COLOR_LIGHT_GREEN
    elif color == '10':
        return COLOR_BOLD_BLUE
    elif color == '11':
        return COLOR_BLUE
    elif color == '12':
        return COLOR_LIGHT_BLUE
    elif color == '13':
        return COLOR_PINK
    elif color == '14':
        return COLOR_DARK_PINK
    else:
        print(f'Unknown color: {color}')
        return None

def main():
    tt = DemoBoard.get()
    
    if not load_project(tt):
        return
    
    # Set freq to 40MHz
    tt.clock_project_PWM(40e6)
    
    # CS - chip select, active low
    tt.uio_oe_pico[0] = 1
    tt.uio_in[0] = 1
    
    #spi = SoftSPI(baudrate=int(20e6), polarity=0, phase=1, bits=8, sck=tt.pins.pin_uio3, mosi=tt.pins.pin_uio1, miso=tt.pins.pin_uio2) #firstbit=MSB
    
    spi = PIOSPI(sm_id=0, pin_mosi=tt.pins.pin_uio1, pin_miso=tt.pins.pin_uio2, pin_sck=tt.pins.pin_uio3, cpha=True, cpol=False, freq=int(20e6))

    #tt.pins.pin_uio4.irq(trigger=Pin.IRQ_FALLING, handler=isr_line)
    #tt.pins.pin_uio5.irq(trigger=Pin.IRQ_FALLING, handler=isr_frame)

    misc = int('00110', 2)

    while 1:
        print('Please input action and press enter: ')
        print('0 - Set background')
        print('1 - Set COLOR0')
        print('2 - Set COLOR1')
        print('3 - Set COLOR2')
        print('4 - Set COLOR3')
        print('5 - Set sprite to SPRITE_DRINK')
        print('6 - Set sprite to SPRITE_HEART')
        print('7 - Set sprite to SPRITE_SPIRAL')
        print('8 - Set sprite to SPRITE_TT')
        print('9 - Toggle sprite transparency')
        print('10 - Toggle sprite movement')
        
        input = sys.stdin.readline().rstrip()
        print(f'"{input}"')

        if input == '0':
            print('Please choose background (0 - 3):')
            
            background = sys.stdin.readline().rstrip()
            
            if background == '0':
                misc &= ~0b11
                misc |= 0
                send_cmd(tt, spi, CMD_MISC, misc.to_bytes(1, 'little'))
            elif background == '1':
                misc &= ~0b11
                misc |= 1
                send_cmd(tt, spi, CMD_MISC, misc.to_bytes(1, 'little'))
            elif background == '2':
                misc &= ~0b11
                misc |= 2
                send_cmd(tt, spi, CMD_MISC, misc.to_bytes(1, 'little'))
            elif background == '3':
                misc &= ~0b11
                misc |= 3
                send_cmd(tt, spi, CMD_MISC, misc.to_bytes(1, 'little'))
            else:
                print(f'Unknown background: {background}')
        elif input == '1':
            color = choose_color()
            if color:
                send_cmd(tt, spi, CMD_COLOR1, color)
        elif input == '2':
            color = choose_color()
            if color:
                send_cmd(tt, spi, CMD_COLOR2, color)
        elif input == '3':
            color = choose_color()
            if color:
                send_cmd(tt, spi, CMD_COLOR3, color)
        elif input == '4':
            color = choose_color()
            if color:
                send_cmd(tt, spi, CMD_COLOR4, color)
        elif input == '5':
            send_cmd(tt, spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_DRINK))
        elif input == '6':
            send_cmd(tt, spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_HEART))
        elif input == '7':
            send_cmd(tt, spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_SPIRAL))
        elif input == '8':
            send_cmd(tt, spi, CMD_SPRITE_DATA, sprite2bytes(SPRITE_TT)) 
        elif input == '9':
            misc ^= 1<<3
            send_cmd(tt, spi, CMD_MISC, misc.to_bytes(1, 'little'))
        elif input == '10':
            misc ^= 1<<2
            send_cmd(tt, spi, CMD_MISC, misc.to_bytes(1, 'little'))
        else:
            print(f'Unknown command: {input}')

"""
>>> import examples.tt_um_top_mole99 as test
>>> test.run()
"""
