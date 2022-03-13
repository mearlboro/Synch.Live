#!/usr/bin/python3

from ws2801_headset import WS2801Headset

# initialise logging to file
import logger

leds = WS2801Headset((0,0,0), (0,127,0), 2, 1)
leds.pilot()
