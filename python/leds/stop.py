#!/usr/bin/python3

from leds.ws2801_headset import WS2801Headset

# initialise logging to file
import leds.logger

leds = WS2801Headset((0,0,0), (0,0,0), 2, 1)
leds.all_off()
