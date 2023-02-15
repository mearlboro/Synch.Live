import cv2
import datetime
import imutils
import logging
import numpy as np
import sys

from types import SimpleNamespace
from typing import Any, List, Tuple, Optional, Union

# initialise logging to file
import synch_live.camera.core.logger

class Detector():
    def __init__(self, config: SimpleNamespace) -> None:
        """
        Initialise a simple, colour-based object detector with the minimum and
        maximum perimeters and the lower and upper colour bounds in `config`.

        Params
        ------
        config
            namespace (dot-addressible dict) including configuration for the
            detector, such as the following parameters:

            min_contour, max_contour : int
                minimum and maximum perimeter a rectangle requires to be detected
            min_hsv, max_hsv         : np.ndarray
                numpy arrays of shape (3,) where the elements represent HSV values to
                be used as colour range for the objects to be detected
        """
        def to_hsv(hsv):
            return np.array([ hsv.hue, hsv.saturation, hsv.value], np.uint8)

        self.config = config
        self.min_hsv = to_hsv(config.min_colour)
        self.max_hsv = to_hsv(config.max_colour)


    def log_detected(self,
            boxes: List[Tuple[float, float, float, float]]
        ) -> None:
        """
        Write detected boxes to logfile

        Side-effects
        ------
        Write to logfile
        """
        for i, box in enumerate(boxes):
            logging.info(f'{i+1}, {box}')

        if len(boxes):
            logging.info(f"Found {len(boxes)} blobs in frame.")


    def draw_bbox(self,
            frame:  np.ndarray,
            player: int,
            rect:   Tuple[float, float, float, float]
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
            ( x, y, width, height ), normalised to the size of the image

        Returns
        ------
            updated frame
        """

        (x, y, w, h) = rect

        try:
            frame = cv2.rectangle(frame, (int(x), int(y), int(w), int(h)),
                (0, 0, 255), 2)
            frame = cv2.putText(frame, f"Player{player}", (int(x), int(y)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 0, 255))
        except OverflowError:
            logging.info(f"Cannot draw bbox with coordinates {x}, {y}, {w}, {h}")

        return frame


    def draw_annotations(self,
            frame: np.ndarray, boxes: List[Tuple[float, float, float, float]],
            normalised: bool = True, extra_text: str = ''
        ) -> np.ndarray:
        """
        Draws all necessary annotations (timestamp, tracked objects)
        onto the given frame

        Params
        ------
        frame
            a single frame of a cv2.VideoCapture() or picamera stream
        boxes
            a list of 4-element tuples with the coordinates and size of rectangles
            ( x, y, width, height ), that may be normalised to the size of the image
        normalsied
            if set, then the boxes are normalised with image size, so they need to
            be multiplied with the image size

        Returns
        -----
            updated frame
        """
        # Obtain frame width and height
        fw = frame.shape[1]
        fh = frame.shape[0]

        timestamp = datetime.datetime.now()
        frame = cv2.putText(frame, timestamp.strftime("%y-%m-%d %H:%M:%S"),
                    (10, fh - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1)

        frame = cv2.putText(frame, extra_text,
                    (fw - 120, fh - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1)

        for i, box in enumerate(boxes):
            # draw rectangle and label over the objects position in the video
            if normalised:
                (x, y, w, h) = box
                box = (x * fw, y * fh, w * fw, h * fh)

            frame = self.draw_bbox(frame, i + 1, box)

        return frame


    def detect_colour(self,
            frame: np.ndarray,
            dump: bool = False
        ) -> List[Tuple[float, float, float, float]]:
        """
        Gets the initial regions of interest (ROIs) to be tracked, which are green
        LEDs in a dark image. Uses a conversion to hue-saturation-luminosity to pick
        out the green objects in the image, and a dilation filter to emphasise the
        point-sized ROIs into bigger objects.

        Params
        ------
        frame
            a single frame of a cv2.VideoCapture() or picamera stream
        dump
            if set, save processing steps as images for debugging

        Returns
        ------
            a list of tuples, with the coordinates of the bounding boxes of the
            detected objects

        Side-effects
        ------
            centre of mass coordinates are logged for the detected boxes
        """
        # Convert the frame in RGB color space to HSV
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # create image mask by selecting the range of green hues from the HSV image
        green_mask = cv2.inRange(hsv_frame, self.min_hsv, self.max_hsv)

        if dump:
            cv2.imwrite(f"{self.config.server.IMG_PATH}/hsv_frame.jpg" , hsv_frame)
            cv2.imwrite(f"{self.config.server.IMG_PATH}/green_mask.jpg", green_mask)

        # we look for punctiform green objects, so perform image dilation on mask
        # to emphasise these points
        kernel = np.ones((5, 5), "uint8")
        green_mask = cv2.dilate(green_mask, kernel)
        if dump:
            cv2.imwrite(f"{self.config.server.IMG_PATH}/green_mask_dilated.jpg", green_mask)

        res = cv2.bitwise_and(frame, frame, mask = green_mask)
        if dump:
            cv2.imwrite(f"{self.config.server.IMG_PATH}/img_masked.jpg", res)
        res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)

        # Find the contours of all green objects
        contours, hierarchy = cv2.findContours(res,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE)

        # Obtain frame width and height
        fw = frame.shape[1]
        fh = frame.shape[0]

        bboxes = []
        # go through detected contours and reject if not the wrong size or shape
        for i, contour in enumerate(contours):
            box = cv2.contourArea(contour)
            if(box >= self.config.min_contour and box <= self.config.max_contour):
                x, y, w, h = cv2.boundingRect(contour)

                if (w / h >= 0.8 or w / h <= 1.2):
                    bboxes.append((x/fw, y/fh, w/fw, h/fh))

        self.log_detected(bboxes)

        return bboxes
