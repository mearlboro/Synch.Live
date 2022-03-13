#!/usr/bin/python3

import importlib
import logging
import random
import time
from typing import List, Tuple

# hardware controllers
import Adafruit_WS2801 as LED
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO

# initialise logging to file
import logger

# import abstract headset class
from headset import Headset

"""
Class implementing the behaviour of a LED headset on an actual RaspberryPi
using the WS2801 LEDs
"""
class WS2801Headset(Headset):

    """
    The characteristic values for the first version of the headset are hardcoded
    here. If you're building a new type of headset make sure to update.
    """
    COUNT       = 30
    CROWN_RANGE = list(range(26))
    PILOT_RANGE = [ 28 ]


    def __init__(self,
            crown_col: Tuple[int, int, int], pilot_col: Tuple[int, int, int],
            on_delay: float, off_delay: float,
            count: int             = COUNT,
            crown_range: List[int] = CROWN_RANGE,
            pilot_range: List[int] = PILOT_RANGE,
            ) -> None:
        """
        Initialise WS2801 pixel array. The array is split into two parts, the 'crown'
        which will blink and the 'pilot' light which must be always on and pure green.

        Params
        ------
        crown_col, pilot_col
            (r, g, b) values for the colour of the crown and pilot lights respectively

        on_delay, off_delay
            time (in seconds) the crown lights should be on, and off, respectively

        count
            total number of LEDs on the headset

        crown_range, pilot_range
            a list of indexes for the LEDS used in the crown (blinking) or as pilot
            lights (not blinking) respectively

        """

        super().__init__(crown_col, pilot_col, on_delay, off_delay, pilot_turnon = False)

        self.CROWN_RANGE = crown_range
        self.PILOT_RANGE = pilot_range

        SPI_PORT    = 0
        SPI_DEVICE  = 0
        self.pixels = LED.WS2801Pixels(count, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

        logging.info('Initialisation of WS2801 LEDs complete')

        self.pilot()


    def all_off(self) -> None:
        """
        Turn off all LEDs in the headset
        """
        self.pixels.clear()
        self.pixels.show()
        super().all_off()


    def pilot(self) -> None:
        """
        Turn on all LEDs in the pilot range in the headset
        """
        for i in self.PILOT_RANGE:
            self.pixels.set_pixel(i, LED.RGB_to_color(*self.pilot_col))
        self.pixels.show()
        super().pilot()


    def crown_on(self) -> None:
        """
        Turn on all LEDS in the crown range in the headset
        """
        for i in self.CROWN_RANGE:
            self.pixels.set_pixel(i, LED.RGB_to_color(*self.crown_col))
        self.pixels.show()
        super().crown_on()

    def crown_off(self) -> None:
        """
        Turn off all LEDS in the crown range in the headset
        """
        for i in self.CROWN_RANGE:
            self.pixels.set_pixel(i, LED.RGB_to_color(0, 0, 0))
        self.pixels.show()
        super().crown_off()


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
        if rand > 0:
            r = random.uniform(0, rand)
        else:
            r = 0

        logging.info(f'Waiting {round(r,3)}')
        time.sleep(r)
        self.crown_on()
        time.sleep(self.ON_DELAY)
        self.crown_off()
