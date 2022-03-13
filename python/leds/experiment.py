#!/usr/bin/python3

import asyncio
import aiohttp
import logging
import sys
import time
from typing import Optional

from headset import Headset
from mockloop import mock_loop

# initialise logging to file
import logger

PSI_URL = 'http://observer:8888/psi'

async def fetch_psi() -> Optional[float]:
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(PSI_URL) as resp:
                r = await resp.json()
                return r
    except:
        logging.info("Exception in fetching psi")
        return None

async def loop(leds: Headset, period: float, rand: float) -> None:
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
        psi = await fetch_psi()
        logging.info(f"Psi {psi}")

        if psi is None:
            logging.info("Psi was not fetched: entering mock synchronous loop")
            return
        if psi > 0:
            rand -= 0.1
        else:
            rand += 0.1

        if rand > leds.OFF_DELAY:
            rand = leds.OFF_DELAY
        if rand < 0:
            rand = 0
        logging.info(f'Rand: {rand}')

        time.sleep(next(gen))
        logging.info(f'Tick')

        leds.crown_blink_wait(rand)


if __name__ == "__main__":

    server_type='player'
    if len(sys.argv) > 1:
        server_type = sys.argv[1]

    if server_type == 'player':
        from ws2801_headset import WS2801Headset

        leds = WS2801Headset((127, 63, 0), (0, 255, 0), 0.5, 2.5)
    elif server_type == 'local':
        leds = Headset((127, 63, 0), (0, 255, 0), 0.5, 2.5)

    print(f"Starting {server_type} experiment")

    rand   = leds.OFF_DELAY
    period = leds.OFF_DELAY + leds.ON_DELAY

    print(f"Rand {rand} and period {period}")

    asyncio.run(loop(leds, period, rand))
    asyncio.run(mock_loop(leds, period, 0.5))
