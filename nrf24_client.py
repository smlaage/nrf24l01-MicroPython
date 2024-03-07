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
SERVO_MIN, SERVO_MAX = const(1000), const(9000)
# Timing
LOOP_DELAY = const(100)
POLL_DELAY = const(3)
TIMEOUT_CNT = const(20)
MAX_ERROR = const(20)


def set_error():
    """ Sets the control led to indicate that something went wrong """
    ctrl_led_green.value(0)
    ctrl_led_red.value(1)


def clear_error():
    """ Sets the control led showing that everything is fine """
    ctrl_led_green.value(1)
    ctrl_led_red.value(0)


def get_data():
    """ Sends 'D' to the server and waits for joystick and button data from server.
        Returns success, x, y buttons"""
    nrf.stop_listening()
    send_buf = bytearray(PAYLOAD_SIZE)
    send_buf[0] = ord('D')
    success = True
    x, y, buttons = 0, 0, 0
    
    # Send a request for data
    try:
        nrf.send(send_buf)
    except OSError:
        print("get_data: send failure")
        success = False
        
    nrf.start_listening()
        
    if success:
        for cnt in range(TIMEOUT_CNT):
            if nrf.any():
                recv_buf = nrf.recv()
                x = 256 * recv_buf[0] + recv_buf[1]
                y = 256 * recv_buf[2] + recv_buf[3]
                buttons = recv_buf[4]
                break
            else:
                utime.sleep_ms(POLL_DELAY)
        if cnt > 5:
            print(cnt)
        if cnt >= TIMEOUT_CNT - 1:
            print("get_data: timeout")
            success = False

    if success:
        clear_error()
    else:
        set_error()
    
    return success, x, y, buttons


def set_led(status):
    """ Sends 'L' to the server followed by a byte indicating the LED status
        0 -> off, anything else -> on
        Returns success (True -> okay, False -> failure) """
    
    nrf.stop_listening()
    send_buf = bytearray(PAYLOAD_SIZE)
    send_buf[0] = ord('L')
    send_buf[1] = status
    success = True
        
    # Send led status
    try:
        nrf.send(send_buf)
    except OSError:
        print("set_led: send failure")
        success = True
    
    nrf.start_listening()
    
    if success:
        clear_error()
    else:
        set_error()
        
    return success


# main program starts here ----------------------------------------

# Global variables
bt_old = 1
success_cnt, error_cnt = 0, 0
errors_in_a_row = 0

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
csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]
nrf = NRF24L01(spi, csn, ce, payload_size=PAYLOAD_SIZE)
nrf.set_channel(CHANNEL)
nrf.set_power_speed(POWER, SPEED_250K)
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

# Start the client
print("NRF24L01 client sending on channel", CHANNEL)
print(POWER_DCT[POWER])

try:
    while True:
        
        success, x, y, buttons = get_data()
        if success:
            servo_pos = round(SERVO_MIN + (SERVO_MAX - SERVO_MIN) * x / 65536)
            servo.duty_u16(servo_pos)
            errors_in_a_row = 0
            success_cnt += 1
        else:
            errors_in_a_row += 1
            error_cnt += 1
            print("Error Cnt:", error_cnt)
        
        utime.sleep_ms(LOOP_DELAY)
        
        if bt.value() != bt_old:
            bt_old = bt.value()
            print("Sending button", bt.value())
            success = set_led(not bt.value())
            utime.sleep_ms(LOOP_DELAY)
            
        if errors_in_a_row >= MAX_ERROR:
            print("NRF24L01 client: too many errors! Client stopped!")
            break
        
except KeyboardInterrupt:
    pass

ctrl_led_green.value(0)
ctrl_led_red.value(0)
print()
print("Successes:", success_cnt,
      "  Errors:", error_cnt,
      "  Percent:", round(success_cnt * 100 / (success_cnt + error_cnt), 2))
