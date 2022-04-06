from types import SimpleNamespace
import cv2
from collections import OrderedDict
import datetime
from imutils.video import FileVideoStream, VideoStream
import logging
import numpy as np
import os
import threading
import time

from typing import Any, Dict, List, Tuple, Generator

# initialise logging to file
import camera.core.logger

# import tracking code
from camera.core.emergence import EmergenceCalculator, compute_macro
from camera.core.detection import Detector
from camera.core.tracking  import EuclideanMultiTracker

def compute_macro(X: np.ndarray) -> np.ndarray:
    """
    """
    V = np.mean(X, axis = 0)
    V = V[np.newaxis, :]
    return V

def unwrap_resolution(resolution: SimpleNamespace):
    return (resolution.width, resolution.height)

class Camera():
    def __init__(self, cam_type, config = SimpleNamespace):
        """
        define config
        """
        self.config = config
        self.cam_type = cam_type

        
    def start(self):
        if self.cam_type == 'pi':
            resolution = unwrap_resolution(self.config.resolution)
            self.video_stream_obj = VideoStream(usePiCamera = 1,
                resolution = resolution, framerate = self.config.resolution)
            self.video_stream = self.video_stream_obj.start()

            ## set picam defaults
            self.picamera = self.video_stream_obj.stream.camera
            self.picamera.iso = self.config.iso
            self.picamera.saturation = self.config.saturation
            self.picamera.shutter_speed = self.config.shutter_speed
            self.picamera.awb_mode = self.config.awb_mode

            time.sleep(2)
        elif type(self.cam_type) is int:
            # handle generic camera stream
            pass
        else:
            if not os.path.isfile(self.cam_type):
                raise ValueError(f'No such file: {self.cam_type}')

            self.video_stream = FileVideoStream(self.cam_type).start()
        return self.video_stream

class VideoProcessor():
    """
	Helper class which fetches frames from a vidstream, applies object detection
	and tracking, and computes emergence values based on the object positions &
	a macroscopic feature of the system.
    """
    #def __init__(self, use_picamera: bool, task: str = '',
    #        record: bool = True, annotate: bool = True,
    #        video: str = '', record_path = 'media/video'):
    def __init__(self, config: SimpleNamespace,):
        """
        config:
            config.server changes only changed on server restart
		Params
		------
			use_picamera
				enable if it's run on a RaspberryPi system with a PiCamera
            task: { 'emergence', '' }
                if set, after tracking, run a task on the trajectories, specified
                by this param
                # TODO: add new tasks
			record
				enable to dump the video stream to a file to disk, location is
				media/video
			annotate
				enable to show tracking bounding boxes on the stream
			video
				location of video stream if use_picamera is not enabled
        """
        self.config = config
        self.running = False
        
        record = self.config.server.RECORD
        record_path = self.config.server.RECORD_PATH
        if record and os.path.exists(record_path):
            logging.info(f"Recording Enabled, recording to path {record_path}")
            self.record         = record
            self.record_path    = record_path

        # initialize the output frame and a lock used to ensure thread-safe
        # exchanges of the output frames (useful when multiple browsers/tabs
        # are viewing the stream)
        self.output_frame = None

        self.video_stream = None
        self.video_writer = None

        self.tracking_thread = threading.Thread(target=self.tracking)
        self.lock = threading.Lock()


    @property
    def Psi(self) -> float:
        """
        Compute causal emergence for the current state

        Params
        ------
            None

        Returns
        ------
            Psi computation for the positions of all detected points with respect
            to their centre of mass
        """
        return self.psi


    def tracking(self) -> None:
        """
        Tracking process, starting with initial object detection, then fetch a
        new frame and track. Annotate image and produce a streamable output
        via the global `output_frame` variable.

        Params
        ------
            None

        Returns
        ------
            None

        Side-effects
        ------
            - produce a stream in output_frame
            - may acquire or release lock
            - consumes the video stream
            - updates the positions dict every frame
            - logs tracked positions to log file
        """
        # read the first frame and detect objects
        with self.lock:
            frame = self.video_stream.read()
            if self.record:
                self.video_writer.write(frame)

        if frame is None:
            logging.info('Error reading first frame. Exiting.')
            exit(0)

        bboxes  = self.detector.detect_colour(frame)
        tracker = EuclideanMultiTracker(self.config.tracking)
        self.positions = tracker.update(bboxes)

        if self.config.tracking.annotate:
            frame = self.detector.draw_annotations(frame, self.positions)

        # acquire the lock, set the output frame, and release the lock
        with self.lock:
            self.output_frame = frame.copy()

        # loop over frames from the video stream and track
        while self.running:
            with self.lock:
                frame = self.video_stream.read()

                if frame is not None and self.record:
                    self.video_writer.write(frame)

            if frame is not None:
                bboxes = self.detector.detect_colour(frame)
                self.positions = tracker.update(bboxes)

                if self.config.game.task == 'emergence':
                    if len(self.positions) > 1:
                        # compute emergence of positions and update psi
                        X = [ [ x + w/2, y + h/2 ]
                                for (x, y, w, h) in self.positions ]
                        self.psi = self.calc.update_and_compute(np.array(X))

                if self.config.tracking.annotate:
                    frame = self.detector.draw_annotations(frame, self.positions)

                # acquire the lock, set the output frame, and release the lock
                with self.lock:
                    self.output_frame = frame.copy()


    def generate_frame(self) -> Generator[bytes, None, None]:
        """
        Encode the current output frame as a bytearray of a JPEG image

        Params
        ------
            None

        Returns
        ------
            a generator that produces a stream of bytes with the frame wrapped
            in a HTML response
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


    def start(self) -> None:
        """
        Initialises camera stream, tasks and runs tracking process in a thread.
        Ensures only one tracking thread is running at a time.
        """
        # prevent starting tracking thread if one is already running
        if not self.tracking_thread.is_alive():
            # reinitialise tracking_thread in case previous run crashed
            self.tracking_thread = threading.Thread(target=self.tracking)
            
            self.camera = Camera(self.config.server.CAMERA, self.config.camera)
            self.video_stream = self.camera.start()
            self.detector = Detector(self.config.detection)

            # define video writer to save the stream
            if self.record:
                codec = cv2.VideoWriter_fourcc(*'MJPG')
                date  = datetime.datetime.now().strftime('%y-%m-%d_%H%M')
                resolution = unwrap_resolution(self.config.camera.resolution)
                self.video_writer = cv2.VideoWriter(f'{self.record_path}/output_{date}.avi', codec,
                    self.config.camera.framerate, resolution)

            # positions of tracked objects
            self.positions = []

            # initialise emergence calculator
            self.psi  = 0
            if self.config.game.task == 'emergence':
                logging.info("Initilised EmergenceCalculator")
                self.calc = EmergenceCalculator(compute_macro)
            elif self.config.game.task == '':
                logging.info("No task specified, continuing")

            logging.info("Initialised VideoProcessor with params:")
            logging.info(f"camera type: {self.config.server.CAMERA}")
            logging.info(f"task: {self.config.game.task}")
            logging.info(f"record: {self.record}")
            logging.info(f"annotate: {self.config.tracking.annotate}")

            self.running = True
            self.tracking_thread.start()
            self.lock = threading.Lock()


    def stop(self) -> None:
        """
        Release the video stream and writer pointers and gracefully exit the JVM

        Params
        ------
            None

        Returns
        ------
            None
        """
        logging.info('Stopping tracking thread...')
        self.running = False

        if self.video_stream:
            logging.info('Closing video streamer...')
            self.video_stream.stop()

        if self.record:
            if self.video_writer:
                logging.info('Closing video writer...')
                self.video_writer.release()

        if self.task == 'emergence':
            logging.info('Closing JVM...')
            self.calc.exit()
