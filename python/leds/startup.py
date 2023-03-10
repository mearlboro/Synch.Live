#!/usr/bin/python3

from leds.ws2801_headset import WS2801Headset

# initialise logging to file
import leds.logger

leds = WS2801Headset((0,0,100), (0,255,0), 0.5, 1.5)
while True:
    leds.crown_breathe()
