#!/usr/bin/python3

from abc import ABC
import importlib
import logging
import random
import time
from typing import List, Tuple

# initialise logging to file
import logger

"""
The characteristic values for the first version of the headset are hardcoded
here. If you're building a new type of headset make sure the below reflect
your setup.
"""
COUNT       = 30
CROWN_RANGE = list(range(26))
PILOT_RANGE = [ 28 ]


"""
Abstract class implementing the main behaviour of the LED headset
"""
class Headset(ABC):
    def __init__(self,
            crown_col: Tuple[int, int, int], pilot_col: Tuple[int, int, int],
            on_delay: float, off_delay: float, pilot_turnon: bool = True
        ) -> None:
        """
        Initialise abstract class (also useful for mocking the headset on a dev
        environment

        Params
        ------
        crown_col, pilot_col
            (r, g, b) values for the colour of the crown and pilot lights respectively

        on_delay, off_delay
            time (in seconds) the crown lights should be on, and off, respectively

        pilot_turnon
            if set, turn on the pilot light once initialisation is complete
        """
        self.crown_col = crown_col
        self.pilot_col = pilot_col

        self.ON_DELAY  = on_delay
        self.OFF_DELAY = off_delay

        logging.info('Initialisation complete for colour and delay')

        if pilot_turnon:
            self.pilot()


    def all_off(self) -> None:
        """
        Turn off all LEDs in the headset
        """
        logging.info('All off')


    def pilot(self) -> None:
        """
        Turn on all LEDs in the pilot range in the headset
        """
        logging.info('Pilot on')


    def crown_on(self) -> None:
        """
        Turn on all LEDS in the crown range in the headset
        """
        logging.info('Crown on')

    def crown_off(self) -> None:
        """
        Turn off all LEDS in the crown range in the headset
        """
        logging.info('Crown off')


    def crown_blink(self) -> None:
        """
        All LEDs in the crown should turn on for ON_DELAY time, then turn off
        """
        self.crown_on()
        time.sleep(self.ON_DELAY)
        self.crown_off()

    def crown_blink_wait(self, rand: float) -> None:
        """
        All LEDs in the crown should be on for ON_DELAY time, then off for
        OFF_DELAY.

        This function must be called by a periodic timer with a period equal
        to ON_DELAY + OFF_DELAY.

        When the headsets are not synchronised, the lights may not blink on the
        clock, but instead incur a random delay, controlled by the rand param.

        The amount of time delay is chosen uniformly at random from a range
        given by the parameter.
        """
        if rand:
            r = random.uniform(0, rand)
        else:
            r = 0

        logging.info(f'Waiting {round(r,3)}')
        time.sleep(r)
        self.crown_on()
        time.sleep(self.ON_DELAY)
        self.crown_off()
