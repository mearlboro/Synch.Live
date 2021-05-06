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
MIN_DETECT_COLOUR = np.array([20, 104, 70], np.uint8)
MAX_DETECT_COLOUR = np.array([100, 255, 255], np.uint8)
MIN_DETECT_CONTOUR = 100
MAX_DETECT_CONTOUR = 200

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


def _drawTracked(
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

    Side-effects
    -----
        log timestamp and centre of mass of detected boxes
    """
    (x, y, w, h) = rect
    frame = cv2.rectangle(frame, (x, y, w, h), (0, 255, 0), 2)

    cv2.putText(frame, f"Player{player}", (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5, (0, 255, 0))

    # log x,y coordinate of bounding rectangle centre of mass
    logging.info((player, x + w/2.0, y + h/2.0))

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

    Side-effects
    -----
        log timestamp and centre of mass of detected boxes
    """
    timestamp = datetime.datetime.now()
    cv2.putText(frame, timestamp.strftime("%y-%m-%d %H:%M:%S"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, (255, 255, 255), 1)

    for i, box in enumerate(trackingBoxes):
        # draw rectangle and label over the objects position in the video
        _drawTracked(frame, i, tuple([int(x) for x in box]))

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
        updated frame with bounding boxes drawn on the video

        a list of tuples, with the coordinates of the bounding boxes of the
        detected objects, and the image with bounding boxes drawn on
    """
    # Resize image to make tracking easier
    frame = imutils.resize(frame, width=400)

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

    trackingBoxes = []

    for i, contour in enumerate(contours):
        box = cv2.contourArea(contour)
        # if the area of the detected object is big enough, but not too big
        if(box >= MIN_DETECT_CONTOUR and box <= MAX_DETECT_CONTOUR):
            x, y, w, h = cv2.boundingRect(contour)

            # make them slightly larger to help the tracking
            trackingBoxes.append((x - 1, y - 1, w + 1, h + 1))

    logging.info(f"Found {len(trackingBoxes)} boxes in frame")
    frame = drawAnnotations(frame, trackingBoxes)

    return frame, trackingBoxes


def trackObjects(camera: PiCamera):
    """
    Perform object detection on the first frame and proceed to object tracking

    Params
    ------
    camera
        the PiCamera object, produces a stream of numpy arrays as frames, and
        colours are encoded as BGR rather than RGB

    Returns
    ------
        trajectories of tracked objects

    Side-effects
    ------
        display the bounding boxes and object identifiers on the video
        exit when the key pressed is Esc
    """
    frameNo = 0
    multiTracker = cv2.MultiTracker_create()
    trackingBoxes = []
    
    rawCapture = PiRGBArray(camera)

    for frame in camera.capture_continuous(rawCapture, format="bgr",
            use_video_port="true"):

        image = frame.array

        if frame is None:
            logging.info('Error reading first frame. Exiting.')
            exit(0)

        if frameNo == 0:
            logging.info('First detecting all objects in frame')
            frame, trackingBoxes = detectObjectsInFrame(image)

            for box in trackingBoxes:
                multiTracker.add(createTrackerByName('CSRT'), image, box)

        else:
            return
            success, newBoxes = multiTracker.update(image)

            if not success:
                logging.info(f"Tracking failed at frame {frameNo}")

            for i, box in enumerate(newBoxes):
                drawTracked(frame, i, tuple([int(x) for x in box]))

        rawCapture.truncate(0)
        frameNo += 1


