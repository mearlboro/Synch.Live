#!/usr/bin/python3

from ws2801_headset import WS2801Headset

# initialise logging to file
import synch_live.camera.core.logger

leds = WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5)
while True:
    leds.crown_breathe()
