import cv2
from collections import OrderedDict
import datetime
from imutils.video import VideoStream
import logging
import numpy as np
from picamera import PiCamera
import threading
import time

from typing import Any, List, Tuple, Generator

# initialise logging to file
import logger

# import tracking code
from detection import detect_colour, draw_annotations
from tracking  import EuclideanMultiTracker

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
output_frame = None
lock = threading.Lock()

# initialize the video stream and allow the sensor to warm up
video_stream = VideoStream(usePiCamera=1, resolution=(640,480), framerate=12).start()
time.sleep(1)

# define video writer to save the stream
codec = cv2.VideoWriter_fourcc(*'MJPG')
date  = datetime.datetime.now().strftime('%y-%m-%d_%H%M')
video_writer = cv2.VideoWriter(f'output_{date}.avi', codec, 12.0, (640, 480))

positions = OrderedDict()


def tracking(annotate: bool = True, record: bool = True) -> None:
    """
    Tracking process, starting with initial object detection, then fetch a
    new frame and track. Annotate image and produce a streamable output
    via the global output_frame variable.

    Side-effects
    ------
        - produce a stream in output_frame
        - may acquire or release lock
        - consumes the video stream
        - updates the players dict every frame
        - logs tracked positions to log file
    """
    global video_stream, video_writer, output_frame, lock, positions

    # read the first frame and detect objects
    with lock:
        frame = video_stream.read()
        if record:
            video_writer.write(frame)

    if frame is None:
        logging.info('Error reading first frame. Exiting.')
        exit(0)

    bboxes    = detect_colour(frame)

    tracker   = EuclideanMultiTracker()
    positions = tracker.update(bboxes)

    if annotate:
        frame = draw_annotations(frame, bboxes)

    # acquire the lock, set the output frame, and release the lock
    with lock:
        output_frame = frame.copy()

    # loop over frames from the video stream and track
    while True:
        with lock:
            frame = video_stream.read()
            if record:
                video_writer.write(frame)

        bboxes    = detect_colour(frame)
        positions = tracker.update(bboxes)

        if annotate:
            frame = draw_annotations(frame, bboxes)

        # acquire the lock, set the output frame, and release the lock
        with lock:
            output_frame = frame.copy()


def generate_frame() -> Generator[bytes, None, None]:
    # grab global references to the output frame and lock variables
    global output_frame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if output_frame is None:
                continue
            # encode the frame in JPEG format
            (flag, encoded_frame) = cv2.imencode(".jpg", output_frame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
            bytearray(encoded_frame) + b'\r\n')


def stop() -> None:
    global video_stream, video_writer
    # release the video stream and writer pointers
    video_stream.stop()
    video_writer.release()
