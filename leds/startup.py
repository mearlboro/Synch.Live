#!/usr/bin/python3

from ledcontrol import Headset

# initialise logging to file
import logger

leds = Headset((0,0,0), (0,127,0), 2, 1)
leds.pilot()
