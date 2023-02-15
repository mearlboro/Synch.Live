#!/usr/bin/python
import click

import cv2
import numpy as np

def do_nothing(x):
    pass

@click.command()
@click.option('--filename', help = 'File to open', required = True)
def colour_range(filename):
    """
    Find the colour range of specific objects in the image. Launches a GUI with
    trackbars for hue, saturation and luminosity.

    Press q to quit. The chosen low and high HSV values will be printed.
    """

    window_name = 'Colour range'
    cv2.namedWindow(window_name)

    cv2.createTrackbar('lo_H', window_name, 0,   179, do_nothing)
    cv2.createTrackbar('hi_H', window_name, 179, 179, do_nothing)
    cv2.createTrackbar('lo_S', window_name, 0,   255, do_nothing)
    cv2.createTrackbar('hi_S', window_name, 255, 255, do_nothing)
    cv2.createTrackbar('lo_V', window_name, 0,   255, do_nothing)
    cv2.createTrackbar('hi_V', window_name, 255, 255, do_nothing)

    while(True):
        frame = cv2.imread(filename)
        if frame is None:
            print('Cannot load image, exiting.')
            exit(0)

        lo_HSV = np.array([ cv2.getTrackbarPos('lo_H', window_name),
                            cv2.getTrackbarPos('lo_S', window_name),
                            cv2.getTrackbarPos('lo_V', window_name) ])

        hi_HSV = np.array([ cv2.getTrackbarPos('hi_H', window_name),
                            cv2.getTrackbarPos('hi_S', window_name),
                            cv2.getTrackbarPos('hi_V', window_name) ])

        hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask  = cv2.inRange(hsv, lo_HSV, hi_HSV)
        frame = cv2.bitwise_and(frame, frame, mask = mask)

        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print(lo_HSV)
            print(hi_HSV)
            break

    cv2.destroyAllWindows()


if __name__ == '__main__':
    colour_range()
