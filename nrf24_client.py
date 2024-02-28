"""
NRF24L01 Client

Pins:
   13 -> button to GND, external pullup
   15 -> servo
   16 -> control LED red
   18 -> control LED green

SLW 02/2024
"""

import utime
from machine import Pin, SPI, PWM
from nrf24l01 import NRF24L01, POWER_1, POWER_2, SPEED_250K
from micropython import const

# Constants
POLL_DELAY = const(5)
LOOP_DELAY = const(50)
TIMEOUT = const(50)
SERVO_MIN, SERVO_MAX = const(1000), const(9000)


def get_data():
    """ Sends 'D' to the server and waits for joystick and button data from server.
        Returns success, x, y buttons"""
    send_buf = bytearray((0, 0, 0, 0, 0, 0, 0, 0))
    nrf.stop_listening()
    failure = False
    x, y, buttons = 0, 0, 0
    
    # Send a data request
    ctrl_led_green.value(1)
    try:
        send_buf[0] = ord('D')
        nrf.send(send_buf)
    except OSError:
        print("Send failure")
        ctrl_led_red.value(1)
        failure = True
    else:
        ctrl_led_red.value(0)
        
    if not failure:
              
        # Wait for response with TIMEOUT
        nrf.start_listening()
        start_time = utime.ticks_ms()
        timeout = False
        while not nrf.any() and not timeout:
            if utime.ticks_diff(utime.ticks_ms(), start_time) > TIMEOUT:
                timeout = True
            utime.sleep_ms(POLL_DELAY)

        if timeout:
            print("Timout failure")
            ctrl_led_red.value(1)
            failure = True
        else:
            ctrl_led_red.value(0)
            recv_buf = nrf.recv()
            x = 256 * recv_buf[0] + recv_buf[1]
            y = 256 * recv_buf[2] + recv_buf[3]
            buttons = recv_buf[4]
    ctrl_led_green.value(0)
    return not failure, x, y, buttons


def set_led(status):
    """ Sends 'L' to the server followed by a byte indicating the LED status
        (0 -> off, anything else -> on) """
    
    send_buf = bytearray((ord('L'), status, 0, 0, 0, 0, 0, 0))  
    nrf.stop_listening()
    failure = False
        
    # Send led status
    ctrl_led_green.value(1)
    try:
        nrf.send(send_buf)
    except OSError:
        print("Send failure")
        ctrl_led_red.value(1)
        failure = True
    else:
        ctrl_led_red.value(0)
    
    nrf.start_listening()
    return failure

# main program starts here ----------------------------------------

# Global variables
bt_old = 1

# Initiate buttons, LEDs and servo
ctrl_led_green = Pin(18, Pin.OUT)
ctrl_led_red = Pin(16, Pin.OUT)
bt = Pin(13, Pin.IN)
servo = PWM(Pin(15))
servo.freq(50)

# Initiate nrf24
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
cfg = {"spi": spi, "miso": 4, "mosi": 7, "sck": 6, "csn": 14, "ce": 17}
pipes = ("RCar1".encode('utf-8'), "RCar2".encode('utf-8'))
channel = 105
csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]
nrf = NRF24L01(spi, csn, ce, payload_size=8)
nrf.set_channel(channel)
nrf.set_power_speed(POWER_2, SPEED_250K)
nrf.open_tx_pipe(pipes[0])
nrf.open_rx_pipe(1, pipes[1])
nrf.start_listening()

# Run a short LED show
ctrl_led_red.value(1)
utime.sleep_ms(200)
ctrl_led_red.value(0)
ctrl_led_green.value(1)
utime.sleep_ms(200)
ctrl_led_green.value(0)

print("NRF24L01 client sending on channel", channel)

while True:
    
    success, x, y, buttons = get_data()
    if success:
        # print(x, y, buttons)
        servo_pos = round(SERVO_MIN + (SERVO_MAX - SERVO_MIN) * x / 65536)
        servo.duty_u16(servo_pos)
    utime.sleep_ms(LOOP_DELAY)
    
    if bt.value() != bt_old:
        print("Sending button", bt.value())
        set_led(not bt.value())
        bt_old = bt.value()
        utime.sleep_ms(LOOP_DELAY)
