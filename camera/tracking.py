import cv2
import logging
import numpy as np
import sys

from typing import Any, List, Tuple, Optional, Union

# initialise logging to file
import logger


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


def readVideoFrame(vid: cv2.VideoCapture) -> Optional[np.ndarray]:
    """
    Read a single frame from video

    Params
    ------
    vid
        video file/stream

    Returns
    ------
        numpy array with the data in a single frame

    Side-effects
    ------
        may fail if there are no frames, or stream is interrupted, in which case
        it returns None
    """
    success, frame = vid.read()

    if not success:
        logging.info('Failed to read video')
        return None
    else:
        return frame


def drawTracked(
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

    cv2.putText(frame, f"Player{player}", (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5, (0, 255, 0))

    # log x,y coordinate of bounding rectangle centre of mass
    logging.info((player, x + w/2.0, y + h/2.0))

    return frame


def detectObjectsInFrame(
        frame: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
    """
    Gets the initial regions of interest (ROIs) to be tracked, which are green
    LEDs in a dark image. Uses a conversion to hue-saturation-luminosity to pick
    out the green objects in the image, and a dilation filter to emphasise the
    point-sized ROIs into bigger objects.

    Params
    ------
    frame
        a single frame of a cv2.VideoCapture()

    Returns
    ------
        a list of tuples, with the coordinates of the bounding boxes of the
        detected objects

    Side-effects
    ------
        display the bounding boxes and object identifiers on the video
    """
    # Convert the frame in RGB color space to HSV
    hsvFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Set range for what is the 'darkest' and 'lightest' green color we look for
    green_lower = np.array([25, 52, 72], np.uint8)
    green_upper = np.array([102, 255, 255], np.uint8)

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
        if(box > 20 and box < 100):
            x, y, w, h = cv2.boundingRect(contour)

            # draw rectangle and label over the objects position in the video
            drawTracked(frame, i, (x, y, w, h))

            # make them slightly larger to help the tracking
            trackingBoxes.append((x - 1, y - 1, w + 1, h + 1))

    cv2.imshow('Detection of Synch.Live players', frame)

    return trackingBoxes


def trackObjectsInVideo(
        vid: cv2.VideoCapture, multiTracker: cv2.MultiTracker
    ):
    """
    Tracks objects in given video, drawing a video output with bounding boxes

    Params
    ------
    vid
        video file/stream to track
    multiTracker
        openCV multiTracker initialised with bounding boxes of the objects to
        track

    Returns
    ------
        a list of lists representing trajectories of each object

    Side-effects
    ------
        display the bounding boxes and object identifiers on the video
        exit when the key pressed is Esc
    """

    while vid.isOpened():
        frame = readVideoFrame(vid)

        if frame is None:
            logging.info('Error reading frame from video')
            return

        success, newBoxes = multiTracker.update(frame)

        if not success:
            logging.info('Tracking failed')
            return

        for i, box in enumerate(newBoxes):
            drawTracked(frame, i, tuple([int(x) for x in box]))

        cv2.imshow('Tracking of Synch.live players', frame)
        # wait on any key to move to the next frame, and exit if it's Esc
        if cv2.waitKey(1) & 0xFF == 27:
            return


def trackObjects(videoPath: str):
    """
    Create a VideoCapture object for a video/stream at the given path, then
    perform object detection on the first frame and proceed to object tracking

    Params
    ------
    videoPath
        path of video file or stream

    Returns
    ------
        trajectories of tracked objects

    Side-effects
    ------
        display the bounding boxes and object identifiers on the video
        exit when the key pressed is Esc
    """
    vid = cv2.VideoCapture(videoPath)

    frame = readVideoFrame(vid)
    if frame is None:
        logging.info('Error reading first frame')

    trackingBoxes = detectObjectsInFrame(frame)

    multiTracker = cv2.MultiTracker_create()
    for box in trackingBoxes:
        multiTracker.add(createTrackerByName('CSRT'), frame, box)

    trackObjectsInVideo(vid, multiTracker)

    # vid.stop() # for webcam
    vid.release() # for file

if __name__ == '__main__':

    videoPath = "video/composite.mp4"
    trackObjects(videoPath)

    cv2.destroyAllWindows()

