#!/usr/bin/python3

import logging
import time

from ledcontrol import Headset

# initialise logging to file
import logger


def loop_blink(period):
    """
    This function uses a generator defined below in the tick() function to call
    the Headset function that makes the lights blink with a period given by the
    period parameter

    It uses a global parameter rand to mock an external parameter that reduces
    the randomness incurred in the blinking
    """
    def tick():
        t = time.time()
        while True:
            t += period
            yield max(t - time.time(), 0)

    gen = tick()

    global rand

    while rand > 0:
        time.sleep(next(gen))
        logging.info(f'Tick')

        leds.crown_blink_wait(rand)

        rand -= 0.1

    for _ in range(100):
        time.sleep(next(gen))
        logging.info(f'Tick')

        leds.crown_blink_wait(0)


leds = Headset((127, 63, 0), (0, 255, 0), 0.5, 2.5)

rand   = leds.OFF_DELAY
period = leds.OFF_DELAY + leds.ON_DELAY

loop_blink(period)
