#!/usr/bin/python3

import sys
from ws2801_headset import WS2801Headset

# initialise logging to file
import logger

if len(sys.argv):
    mode = sys.argv[1]

leds = WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5)

if mode == 'pilot':
    leds.pilot()
elif mode == 'breathe':
    while True:
        leds.crown_breathe()
elif mode == 'rainbow':
    while True:
        leds.crown_rainbow()
elif mode == 'exposure':
    leds.crown_on()
    leds.pilot()
else:
    print("Mode is either 'breathe' or 'rainbow', pass as argument")
