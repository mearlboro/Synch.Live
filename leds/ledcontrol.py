#!/usr/bin/python3

from datetime import date
import logging
import random
import time
import RPi.GPIO as GPIO
import Adafruit_WS2801 as LED
import Adafruit_GPIO.SPI as SPI

from typing import List, Tuple

"""
The characteristic values for the first version of the headset are hardcoded
here. If you're building a new type of headset make sure the below reflect
your setup.
"""
COUNT       = 30
CROWN_RANGE = range(26)
PILOT_RANGE = [ 28 ]

class LEDHeadset:

    def __init__(self,
            hostname: str,
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
        hostname
            hostname of the device the current instance of the headset runs on

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
        today = date.today().strftime('%Y%m%d')
        log_path = f"logs/{hostname}_{today}.log"
        logging.basicConfig(filename = log_path, filemode = 'a', level = logging.INFO,
                format = '%(asctime)s.%(msecs)03d %(message)s', datefmt = '%H:%M:%S')

        self.crown_col = crown_col
        self.pilot_col = pilot_col

        self.ON_DELAY  = on_delay
        self.OFF_DELAY = off_delay

        self.CROWN_RANGE = crown_range
        self.PILOT_RANGE = pilot_range

        SPI_PORT    = 0
        SPI_DEVICE  = 0
        self.pixels = LED.WS2801Pixels(count, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

        logging.info('Initialisation complete')


    def all_off(self) -> None:
        """
        Turn off all LEDs in the headset
        """
        self.pixels.clear()
        self.pixels.show()
        logging.info('All off')


    def pilot(self) -> None:
        """
        Turn on all LEDs in the pilot range in the headset
        """
        for i in self.PILOT_RANGE:
            self.pixels.set_pixel(i, LED.RGB_to_color(*self.pilot_col))
        self.pixels.show()
        logging.info('Pilot on')


    def crown_on(self) -> None:
        """
        Turn on all LEDS in the crown range in the headset
        """
        for i in self.CROWN_RANGE:
            self.pixels.set_pixel(i, LED.RGB_to_color(*self.crown_col))
        self.pixels.show()
        logging.info('Crown on')

    def crown_off(self) -> None:
        """
        Turn off all LEDS in the crown range in the headset
        """
        for i in self.CROWN_RANGE:
            self.pixels.set_pixel(i, LED.RGB_to_color(0, 0, 0))
        self.pixels.show()
        logging.info('Crown off')


    def crown_blink(self) -> None:
        """
        All LEDs in the crown should turn on for ON_DELAY time, then turn off
        """
        self.crown_on()
        time.sleep(self.ON_DELAY)
        self.crown_off()

    def crown_blink_wait(self, drift: float) -> None:
        """
        All LEDs in the crown should be on for ON_DELAY time, then off for
        OFF_DELAY.

        When the headsets are not synchronised, the time the headset is off may
        incur a (potentially negative) drift. That is, despite being triggered
        periodically, there might be a rush or a delay until the lights actually
        turn on. Therefore, it first waits and then turns the lights on.

        The amount of time to rush or delay is chosen uniformly at random from
        a range given by the drift parameter.
        """
        r = random.uniform(-drift, drift)

        logging.info('Waiting ' + str(self.OFF_DELAY + r))
        time.sleep(self.OFF_DELAY + r)
        self.crown_on()
        time.sleep(self.ON_DELAY)
        self.crown_off()
