import cv2
import numpy as np

from typing import Dict

def hex_to_hsv(c: str) -> Dict[str, int]:
    """
    Convert from hex to HSV dict, using the ranges of OpenCV

    Params
    ------
    c
        7-digit hex string of the form #ffffff representing a RGB colour

    Returns
    ------
    HSV dict with keys 'hue', 'saturation', 'luminosity' and values in OpenCV ranges
        H: 0-179
        S: 0-255
        V: 0-255
    """

    rgb = np.uint8([[[ int(c[i:j], base = 16) for i,j in [(1,3),(3,5),(5,7)] ]]])
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return { 'hue': hsv[0][0][0], 'saturation': hsv[0][0][1], 'value': hsv[0][0][2] }


def hsv_to_hex(hsv: Dict[str, int]) -> str:
    """
    Convert from HSV dict, to HTML compatible hex colour

    Params
    ------
    HSV dict with keys 'hue', 'saturation', 'luminosity' and values in OpenCV ranges
        H: 0-179
        S: 0-255
        V: 0-255

    Returns
    ------
    7-digit hex string of the form #ffffff representing a RGB colour
    """

    rgb = cv2.cvtColor(np.uint8([[list(hsv.values())]]), cv2.COLOR_HSV2RGB)
    hexs = [ str(hex(i))[2:] for i in rgb[0][0] ]
    hexs = [ f"0{i}" if len(i) == 1 else i for i in hexs ]
    return '#' + ''.join(hexs)

