#!/usr/bin/python3

from abc import ABC
import importlib
import logging
import random
import time
from typing import List, Tuple

# initialise logging to file
import leds.logger

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
        Turn on all LEDS in the crown range in the headset. A specified colour can be passed in as a parameter.
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
        if not col:
            col = self.crown_col
        logging.info(f"Fade into colour {col} for duration {dt * 256}")

    def crown_fade_between_colours(self,
            dt: float = 0.01, col1: Tuple[int, int, int] = (0, 0, 0), col2: Tuple[int, int, int] = (0, 0, 0)
        ) -> None:
        """
        All leds in the crown should fade in to the `col2` param  from 'col1' param in `dt` second
        increments
        """
        logging.info(f"Begin fade from colour {col1} into colour {col2} for duration {dt * 256}")

    def crown_fadeout(self, dt: float = 0.01) -> None:
        """
        All leds in the crown should fade out from the current colour to black,
        going from full brightness to none in `dt` second increments
        """
        logging.info(f"Fade to black for duration {dt * 256}")


    def crown_breathe(self,
            dt: float = 0.01, delay: float = 0, col: Tuple[int, int, int] = (0, 0, 0)
        ) -> None:
        """
        All leds in the crown should fade in to colour specified in `col` param,
        or the `crown_col` set in the constructor if that is not set, in `dt`
        second increents. Then, after `delay` seconds, fade out in `dt` second
        increments
        """
        if not delay:
            delay = self.ON_DELAY
        logging.info(f"Begin breathing effect with {delay} delay")

        self.crown_off()
        self.crown_fadein_colour(dt, col = col)
        time.sleep(delay)
        self.crown_fadeout(dt)
        time.sleep(delay)


    def crown_rainbow(self, dt: float = 0.01) -> None:
        """
        All leds in the crown cycle for `dt` seconds through the 256 possible
        colours, starting from consecutive colours
        """
        logging.info("Cycling through rainbow colours")

    def crown_police(self, dt: float = 1.0) -> None:
        """
        All leds in the crown flash alternative colours for `dt` seconds through either blue
        or red, starting from alternate colours.
        """
        logging.info("Cycling police lights")

    def crown_fire(self, dt: float = 1.0) -> None:
        """
        All leds change between varying shades of red, orange and yellow randomly.
        """
        logging.info("Begin fire animation")

    def crown_party(self, dt: float = 1.0) -> None:
        """
        All leds change between varying disco-esque colours.
        """
        logging.info("Begin party animation")

    def crown_paparazzi(self) -> None:
        """
        Some leds in the crown flash white randomly while others stay black.
        """
        logging.info("Begin paparazzi effect")

    def crown_trial_config_log(self, r=255, g=255, b=255, blink_freq=1, effect_dur=1) -> None:
        """
        Set the colour, blink frequency and effect duration to the custom configuration, and run for 5 seconds.
        """
        logging.info("Begin trial of custom configuration")

    def crown_run_config(self, r=255, g=255, b=255, blink_freq=1, effect_dur=1) -> None:
        """
        Set the colour, blink frequency and effect duration to the custom configuration, and run for 5 seconds.
        """
        logging.info("Begin running of custom configuration")

    def crown_rainbow_repeat(self,
            dt: float = 0.01, duration: float = 2
        ) -> None:
        """
        All leds in the crown cycle for `dt` seconds through the 256 possible
        colours for a total time of `duration` seconds
        """
        logging.info("Begin rainbow cycle effect")
        n = int(duration / dt)

        for _ in range(n):
            self.crown_rainbow()
