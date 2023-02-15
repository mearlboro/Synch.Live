#!/usr/bin/python3

import logging
import time
import typing

from headset import Headset

# initialise logging to file
import logger


def mock_loop(leds: Headset, period: float, rand: float, repeats: int = 100) -> None:
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

    while rand > 0:
        time.sleep(next(gen))
        logging.info(f'Tick')

        leds.crown_blink_wait(rand)

        rand -= 0.1

    for _ in range(repeats):
        time.sleep(next(gen))
        logging.info(f'Tick')

        leds.crown_blink_wait(0)


if __name__ == "__main__":
    from ws2801_headset import WS2801Headset

    leds = WS2801Headset((0, 0, 100), (0, 255, 0), 0.5, 1.5)

    rand   = leds.OFF_DELAY
    period = leds.OFF_DELAY + leds.ON_DELAY

    mock_loop(leds, period, rand)
