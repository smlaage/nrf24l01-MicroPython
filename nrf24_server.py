"""
NRF24L01 Server

GPIO Pins:
    11 -> LED 0
    12 -> LED 1
    13 -> LED 2
    16 -> control LED red
    18 -> control LED green
    19 -> button 0 to GND, external pullup
    20 -> button 1 to GND, external pullup
    26 -> ADC X
    27 -> ADC Y

SLW 02/2024
"""

import utime
from machine import Pin, SPI, ADC
from nrf24l01 import NRF24L01, POWER_0, POWER_1, POWER_2, POWER_3, \
                     SPEED_250K, SPEED_1M
from micropython import const

# Constants
CHANNEL = const(95)
PAYLOAD_SIZE = const(6)
POWER = POWER_1
POWER_DCT = {POWER_0: "Power 0: -18 dBm",
             POWER_1: "Power 1: -12 dBm",
             POWER_2: "Power 2:  -6 dBm",
             POWER_3: "Power 3:   0 dBm"}
# Timing
POLL_DELAY = const(3)
SEND_DELAY = const(4)


def set_error():
    """ Sets the control led to indicate that something went wrong """
    ctrl_led_green.value(0)
    ctrl_led_red.value(1)


def clear_error():
    """ Sets the control led showing that everything is fine """
    ctrl_led_green.value(1)
    ctrl_led_red.value(0)
       

def send_data():
    """ Sends the joystick position (x and y) and the buttons
        as message of 8 bytes """
    nrf.stop_listening()
    x, y = adcx.read_u16(), adcy.read_u16()
    buttons = 0
    success = True
    if bt_0.value() == 0:
        buttons += 1
    if bt_1.value() == 0:
        buttons += 2
    send_buf = bytearray(PAYLOAD_SIZE)
    send_buf[0] = x // 256
    send_buf[1] = x % 256
    send_buf[2] = y // 256
    send_buf[3] = y % 256
    send_buf[4] = buttons
    try:
        nrf.send(send_buf)
    except OSError:
        print("send_data: send error")
        success = False
    
    if success:
        clear_error()
    else:
        set_error()
        
    nrf.start_listening()
    return success
    
    
def set_leds(msg):
    """ Sets the LEDs on or off """
    for i in range(3):
        if msg[i+1] == 0:
            leds[i].value(0)
        else:
            leds[i].value(1)
    
# main program starts here ----------------------------------------

# Global variables
success_cnt, error_cnt = 0, 0
last_connection = 0

# Initiate ADC, LEDs and buttons
adcx, adcy = ADC(26), ADC(27)
ctrl_led_green = Pin(18, Pin.OUT)
ctrl_led_red = Pin(16, Pin.OUT)
leds = (Pin(11, Pin.OUT), Pin(12, Pin.OUT), Pin(13, Pin.OUT))
bt_0 = Pin(19, Pin.IN)
bt_1 = Pin(20, Pin.IN)

# Initiate nrf24
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
cfg = {"spi": spi, "miso": 4, "mosi": 7, "sck": 6, "csn": 14, "ce": 17}
pipes = ("RCar1".encode('utf-8'), "RCar2".encode('utf-8'))
csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]
nrf = NRF24L01(spi, csn, ce, payload_size=PAYLOAD_SIZE)
nrf.set_channel(CHANNEL)
nrf.set_power_speed(POWER, SPEED_250K)
nrf.open_tx_pipe(pipes[1])
nrf.open_rx_pipe(1, pipes[0])
nrf.start_listening()

# Run a short LED show
ctrl_led_red.value(1)
utime.sleep_ms(200)
ctrl_led_red.value(0)
ctrl_led_green.value(1)
utime.sleep_ms(200)
ctrl_led_green.value(0)
for i in range(3):
     leds[i].value(1)
     utime.sleep_ms(200)
     leds[i].value(0)

# Here we go ...
print("NRF24L01 server listening on channel", CHANNEL)
print(POWER_DCT[POWER])

try:
    while True:
        
        if nrf.any():
            recv_buf = nrf.recv()
            cmd = chr(recv_buf[0])
            
            if cmd.upper() == 'D':   		# get joystick data
                utime.sleep_ms(SEND_DELAY)
                if send_data():
                    success_cnt += 1
                else:
                    error_cnt += 1
                
            elif cmd.upper() == 'L':		# set LEDs
                set_leds(recv_buf)
                
            else:
                print("Command not recognized:", cmd)
        
            last_connection = utime.ticks_ms()
            
        utime.sleep_ms(POLL_DELAY)
        if utime.ticks_ms() > last_connection + 1000:
            ctrl_led_green.value(0)
            ctrl_led_red.value(0)
            
except KeyboardInterrupt:
    pass

print()
if (success_cnt + error_cnt) > 0:
    print("Successes:", success_cnt,
          "  Errors:", error_cnt,
          "  Percent:", round(success_cnt * 100 / (success_cnt + error_cnt), 2))
