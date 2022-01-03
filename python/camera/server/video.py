import cv2
from collections import OrderedDict
import datetime
from imutils.video import FileVideoStream, VideoStream
import logging
import numpy as np
import os
import threading
import time

from typing import Any, List, Tuple, Generator

# initialise logging to file
import camera.core.logger

# import tracking code
from camera.core.emergence import EmergenceCalculator
from camera.core.detection import detect_colour, draw_annotations
from camera.core.tracking  import EuclideanMultiTracker

def compute_macro(X: np.ndarray) -> np.ndarray:
    """
    """
    V = np.mean(X, axis = 0)
    V = V[np.newaxis, :]
    return V


class VideoProcessor():
    """
    """
    def __init__(self, use_picamera: bool, video: str = ''):
        """
        """
        # initialize the output frame and a lock used to ensure thread-safe
        # exchanges of the output frames (useful when multiple browsers/tabs
        # are viewing the stream)
        self.output_frame = None
        self.lock = threading.Lock()

        self.running = True

        # initialize the video stream and allow the sensor to warm up
        if use_picamera:
            self.video_stream = VideoStream(usePiCamera = 1,
                resolution = (640, 480), framerate = 12).start()

            time.sleep(1)
        else:
            if not os.path.isfile(video):
                raise ValueError(f'No such file: {video}')
                exit(0)

            self.video_stream = FileVideoStream(video).start()

        # define video writer to save the stream
        codec = cv2.VideoWriter_fourcc(*'MJPG')
        date  = datetime.datetime.now().strftime('%y-%m-%d_%H%M')
        self.video_writer = cv2.VideoWriter(f'../media/video/output_{date}.avi', codec, 12.0, (640, 480))

        # positions and trajectories of tracked objects
        self.positions = OrderedDict()
        self.trajectories = list()

        # initialise emergence calculator
        self.calc = EmergenceCalculator(compute_macro)
        self.psi  = 0


    @property
    def Psi(self) -> float:
        return self.psi


    def tracking(self, annotate: bool = True, record: bool = True) -> None:
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
        # read the first frame and detect objects
        with self.lock:
            frame = self.video_stream.read()
            if record:
                self.video_writer.write(frame)

        if frame is None:
            logging.info('Error reading first frame. Exiting.')
            exit(0)

        bboxes  = detect_colour(frame)
        tracker = EuclideanMultiTracker()
        self.positions = tracker.update(bboxes)

        if annotate:
            frame = draw_annotations(frame, bboxes)

        # acquire the lock, set the output frame, and release the lock
        with self.lock:
            self.output_frame = frame.copy()

        # loop over frames from the video stream and track
        while self.running:
            with self.lock:
                frame = self.video_stream.read()

                if record:
                    self.video_writer.write(frame)

            if frame is not None:
                bboxes = detect_colour(frame)
                self.positions = tracker.update(bboxes)

                # compute emergence of positions and update psi
                X = [ [ x + w/2, y + h/2 ]
                        for (x, y, w, h) in self.positions.values() ]
                self.psi = self.calc.update_and_compute(np.array(X))

                if annotate:
                    frame = draw_annotations(frame, bboxes)

                # acquire the lock, set the output frame, and release the lock
                with self.lock:
                    self.output_frame = frame.copy()


    def generate_frame(self) -> Generator[bytes, None, None]:
        """
        """
        while self.running:
            # wait until the lock is acquired
            with self.lock:
                # check if the output frame is available, otherwise skip
                # the iteration of the loop
                if self.output_frame is None:
                    continue
                # encode the frame in JPEG format
                (flag, encoded_frame) = cv2.imencode(".jpg", self.output_frame)
                # ensure the frame was successfully encoded
                if not flag:
                    continue
            # yield the output frame in the byte format
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                bytearray(encoded_frame) + b'\r\n')


    def exit(self) -> None:
        """
        Release the video stream and writer pointers and gracefully exit the JVM
        """
        self.running = False

        logging.info('Stopping video streamer...')
        self.video_stream.stop()
        logging.info('Stopping video writer...')
        self.video_writer.release()

        self.calc.exit()
