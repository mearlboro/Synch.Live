#!/usr/bin/python3

from ws2801_headset import WS2801Headset

# initialise logging to file
import synch_live.camera.core.logger

leds = WS2801Headset((0,0,0), (0,0,0), 2, 1)
leds.all_off()
