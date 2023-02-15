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
        self.CROWN_COUNT = len(crown_range)

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


    def crown_fadein_colour(self,
            dt: float = 0.01, col: Tuple[int, int, int] = (0, 0, 0)
        ) -> None:
        """
        All leds in the crown should fade in to the `col` param or, if that is
        not specified, to the `crown_col` set in the constructor in `dt` second
        increments
        """
        super().crown_fadein_colour(dt, col)

        self.crown_off()
        if not (col[0] and col[1] and col[2]):
            col = self.crown_col
        r, g, b = col
        for j in range(100):
            for i in self.CROWN_RANGE:
                self.pixels.set_pixel(i, LED.RGB_to_color(
                        int(r * j/100), int(g * j/100), int(b * j/100)))
            self.pixels.show()
            if dt:
                time.sleep(dt)


    def crown_fadeout(self, dt: float = 0.01) -> None:
        """
        All leds in the crown should fade out from the current colour to black,
        going from full brightness to none in `dt` second increments
        """
        super().crown_fadeout(dt)

        for j in range(100):
            for i in self.CROWN_RANGE:
                r, g, b = self.pixels.get_pixel_rgb(i)
                r = int(r * (100 - j) / 100)
                g = int(g * (100 - j) / 100)
                b = int(b * (100 - j) / 100)
                self.pixels.set_pixel(i, LED.RGB_to_color(r, g, b))
            self.pixels.show()
            if dt:
                time.sleep(dt)


    def crown_breathe(self,
            dt: float = 0.01, delay: float = 0, col: Tuple[int, int, int] = (0, 0, 0)
        ) -> None:
        """
        All leds in the crown should fade in to colour specified in `col` param,
        or the `crown_col` set in the constructor if that is not set, in `dt`
        second increents. Then, after `delay` seconds, fade out in `dt` second
        increments
        """
        super().crown_breathe(dt, delay, col)


    def crown_rainbow(self, dt: float = 0.01) -> None:
        """
        All leds in the crown cycle for `dt` seconds through the 256 possible
        colours, starting from consecutive colours
        """
        super().crown_rainbow(dt)
        for j in range(256):
            for i in self.CROWN_RANGE:
                col = (0, 0, 0)
                pos = ((i * 256 // self.CROWN_COUNT) + j) % 256
                if pos < 85:
                    col = (pos * 3, 255 - pos * 3, 0)
                elif pos < 170:
                    pos -= 85
                    col = (255 - pos * 3, 0, pos * 3)
                else:
                    pos -= 170
                    col = (0, pos * 3, 255 - pos * 3)
                self.pixels.set_pixel(i, LED.RGB_to_color(*col))
            self.pixels.show()
            time.sleep(dt)


    def crown_rainbow_repeat(self,
            dt: float = 0.01, duration: float = 2
        ) -> None:
        """
        All leds in the crown cycle for `dt` seconds through the 256 possible
        colours for a total time of `duration` seconds
        """
        super().crown_rainbow_repeat(dt, duration)

