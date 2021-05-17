import cv2
import datetime
import imutils
import logging
import numpy as np
from picamera import PiCamera
import sys

from typing import Any, List, Tuple, Optional, Union

# initialise logging to file
import logger

# TODO set at calibration time
MIN_DETECT_COLOUR = np.array([50, 104, 70], np.uint8)
MAX_DETECT_COLOUR = np.array([127, 255, 255], np.uint8)
MIN_DETECT_CONTOUR = 100
MAX_DETECT_CONTOUR = 400

def createTrackerByName(name: str) -> Any:
    """
    Create single object tracker.

    Params
    ------
    name
        string name of openCV tracker

    Returns
    ----
    cv2.Tracker onject of that type
    """

    OPENCV_OBJECT_TRACKERS = {
        "CSRT":       cv2.TrackerCSRT_create,
        "KCF":        cv2.TrackerKCF_create,
        "BOOSTING":   cv2.TrackerBoosting_create,
        "MIL":        cv2.TrackerMIL_create,
        "TLD":        cv2.TrackerTLD_create,
        "MEDIANFLOW": cv2.TrackerMedianFlow_create,
        "MOSSE":      cv2.TrackerMOSSE_create
    }

    name = name.upper()
    if (name in OPENCV_OBJECT_TRACKERS.keys()):
        tracker = OPENCV_OBJECT_TRACKERS[name]()
    else:
        tracker = None
        (f'Incorrect tracker name: {name}')

    return tracker


def centreOfMass(box: Tuple[int, int, int, int]) -> Tuple[int, int]:
    """
    Get x,y coordinates for the centre of mass of a box
    """
    (x, y, w, h) = box

    return (x + w/2.0, y + h/2.0)


def drawTrackedObj(
        frame:  np.ndarray,
        player: int,
        rect:   Tuple[int, int, int, int]
    ) -> np.ndarray:
    """
    Draws bounding box of tracked object and object name on the frame

    Params
    ------
    frame
        a single frame of a cv2.VideoCapture()
    player
        the number identifying the current object being tracked
    rect
        a 4-element tuple with the coordinates and size of a rectangle
        ( x, y, width, height )

    Returns
    ------
        updated frame
    """
    (x, y, w, h) = rect
    frame = cv2.rectangle(frame, (x, y, w, h), (0, 255, 0), 2)

    frame = cv2.putText(frame, f"Player{player}", (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5, (0, 255, 0))

    return frame


def drawAnnotations(
        frame: np.ndarray, boxes: List[Tuple[int, int, int, int]]
    ) -> np.ndarray:
    """
    Draws all necessary annotations (timestamp, tracked objects)
    onto the given frame

    Params
    ------
    frame
        a single frame of a cv2.VideoCapture() or picamera stream
    boxes
        a list of 4-element tuples with the coordinates and size
        of rectangles ( x, y, width, height )

    Returns
    -----
        updated frame
    """
    timestamp = datetime.datetime.now()
    frame = cv2.putText(frame, timestamp.strftime("%y-%m-%d %H:%M:%S"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1)

    for i, box in enumerate(boxes):
        # draw rectangle and label over the objects position in the video
        frame = drawTrackedObj(frame, i, tuple([int(x) for x in box]))

    return frame


def detectObjectsInFrame(
        frame: np.ndarray
    ) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
    """
    Gets the initial regions of interest (ROIs) to be tracked, which are green
    LEDs in a dark image. Uses a conversion to hue-saturation-luminosity to pick
    out the green objects in the image, and a dilation filter to emphasise the
    point-sized ROIs into bigger objects.

    Params
    ------
    frame
        a single frame of a cv2.VideoCapture() or picamera stream

    Returns
    ------
        a list of tuples, with the coordinates of the bounding boxes of the
        detected objects

    Side-effects
    ------
        centre of mass coordinates are logged for the detected boxes
    """
    # Convert the frame in RGB color space to HSV
    hsvFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Set range for what is the 'darkest' and 'lightest' green color we look for
    # even the darkest green will be very bright
    green_lower = MIN_DETECT_COLOUR
    green_upper = MAX_DETECT_COLOUR

    # create image mask by selecting the range of green hues from the HSV image
    green_mask = cv2.inRange(hsvFrame, green_lower, green_upper)

    # we look for punctiform green objects, so perform image dilation on mask
    # to emphasise these points
    kernel = np.ones((5, 5), "uint8")
    green_mask = cv2.dilate(green_mask, kernel)

    # Find the contours of all green objects
    contours, hierarchy = cv2.findContours(green_mask,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE)

    # go through detected contours and reject if not the wrong size or shape
    trackingBoxes = []
    for i, contour in enumerate(contours):
        box = cv2.contourArea(contour)
        if(box >= MIN_DETECT_CONTOUR and box <= MAX_DETECT_CONTOUR):
            x, y, w, h = cv2.boundingRect(contour)

            if (w / h >= 0.8 or w / h <= 1.2):
                # make them slightly larger to help the tracking
                trackingBoxes.append((x - 1, y - 1, w + 1, h + 1))

    # log x,y coordinate of bounding rectangle centre of mass
    for i, box in enumerate(trackingBoxes):
        logging.info(f'{i}, {centreOfMass(box)}')

    logging.info(f"Found {len(trackingBoxes)} boxes in frame.")

    return trackingBoxes


def basicMultiTracker(
        frame: np.ndarray, boxes: List[Tuple[int, int, int, int]]
    ) -> List[Tuple[int, int, int, int]]:
    """
    Given contours of objects that were detected in the previous frame detect
    them again in the current frame, then track based on the shortest distance
    from the old contours

    Params
    ------
    frame
        a single frame of a cv2.VideoCapture() or picamera stream
    boxes
        a list of 4-element tuples with the coordinates and size
        of rectangles ( x, y, width, height )

    Returns
    -----
        a list of tuples, with the coordinates of the bounding boxes of the
        detected objects, in the same order as the previous frame
    """
    # keep track of a detected object's centre of mass and preserve order
    oldCM = dict(zip(range(len(boxes)), [ centreOfMass(box) for box in boxes ]))

    # get new positions, centres of mass, and preserve order
    newBoxes = detectObjectsInFrame(frame)
    newBoxesDict = dict()

    # go through new detected boxes and for each find the closest old one
    for box in newBoxes:
        minDist = 10000
        boxId   = -1
        for i in list(oldCM.keys()):
            cmDist = np.linalg.norm(np.array(oldCM[i]) - np.array(centreOfMass(box)))
            if (cmDist < minDist):
                minDist = cmDist
                boxId   = i
        newBoxesDict[boxId] = box

    # return newBoxes in the order of the dictionary keys
    return [v for (k, v) in sorted(newBoxesDict.items())]

