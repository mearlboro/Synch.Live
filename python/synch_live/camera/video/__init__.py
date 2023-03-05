import cv2
from collections import OrderedDict
import datetime

from flask import current_app
from imutils.video import FileVideoStream, VideoStream
import logging
import numpy as np
import os
import threading
import time
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple, Generator
from yaml import safe_load

# initialise logging to file
from ..core import logger

# import relevant project libs
from synch_live.camera.tools.colour import hex_to_hsv
from synch_live.camera.tools.config import parse, unwrap_resolution
from synch_live.camera.core.emergence import EmergenceCalculator, compute_macro
from synch_live.camera.core.detection import Detector
from synch_live.camera.core.tracking import EuclideanMultiTracker

# importing writing in database functions
from synch_live.camera.server.db import *


class Camera():
    def __init__(self, cam_type: Any, config: SimpleNamespace, camera_stream=None) -> None:
        """
        Wrapper around a video stream either fetching frames from a real camera,
        or mocking it using a local video file.

        Params
        ------
        cam_type
            if 'pi', uses a PiCamera on a RaspberryPi
            if a number, fetch the corresponding video stream (e.g. for webcam)
            if a path, simulate a camera using the video at the path
        config
            namespace (dot-addressible dict) including configuration for the
            camera, such as:

            resolution.width, resolution.height : int
            framerate  : int
            iso, shutter_speed, saturation: int
            awb_mode: string
        """
        self.config = config
        self.cam_type = cam_type
        self.camera_stream = camera_stream

    def start(self) -> VideoStream:
        """
        Initialise the video stream according to prameters, set image resolution
        and framerate, as well as camera parameters if PiCamera is used, then
        start the stream

        Side-effects
        ------
        create and start a video stream

        Returns
        ------
        video stream containing the frames fetched from the camera or video
        """
        if self.cam_type == 'pi':
            resolution = unwrap_resolution(self.config.resolution)
            self.video_stream_obj = VideoStream(usePiCamera=1,
                                                resolution=resolution, framerate=self.config.framerate)
            self.video_stream = self.video_stream_obj.start()
            self.picamera = self.video_stream_obj.stream.camera

            ## set picam defaults
            self.update_settings(self.config)

            time.sleep(2)
        elif type(self.cam_type) is int:
            self.video_stream = self.camera_stream
            self.video_stream.start()
        else:
            if not os.path.isfile(self.cam_type):
                raise ValueError(f'No such file: {self.cam_type}')

            self.video_stream = FileVideoStream(self.cam_type).start()

        return self.video_stream

    def update_settings(self, config: SimpleNamespace):
        if self.cam_type == 'pi':
            self.picamera.iso = self.config.iso
            self.picamera.saturation = self.config.saturation
            self.picamera.shutter_speed = self.config.shutter_speed
            self.picamera.awb_mode = self.config.awb_mode


class VideoProcessor():
    """
    Helper class which fetches frames from a vidstream, applies object detection
    and tracking, and computes emergence values based on the object positions &
    a macroscopic feature of the system.
    """

    def __init__(self, config: SimpleNamespace, camera_stream=None):
        """
        Initialise system behaviour and paths using the server configuration in
        config, and videostream, tracker and detector objects

        config:
            config.server changes only changed on server restart

        Params
        ------
        config
            namespace (dot-addressible dict) including config as specified in
            ./camera/config/default.yml

            config.server
                used in the initialisation of the Flask app and the VideoProcessor,
                includes application parameters such as host, port, type of camera,
                whether and where to record
            config.game.task
                used in the VideoProcessor to set up game tasks

                if ''          no task, used for calibration phase
                if 'emergence' use the EmergenceCalculator to compute sync
                if 'manual'    use a slider in the Web UI to set sync
            config.camera
                used in the initialisation of the Camera object, includes camera
                parameters (iso, shutter speed etc), and video parameters
                (resolution and framerate)
            config.tracking
                used in the intialisation of the EuclideanMultiTracker object
            config.detection
                used in the initialisation of the Detector object
        """
        self.config = config
        self.running = False
        self.experiment_id = 'None'

        record = self.config.server.RECORD
        record_path = self.config.server.RECORD_PATH
        if record and os.path.exists(record_path):
            logging.info(f"Recording Enabled, recording to path {record_path}")
            self.record = record
            self.record_path = record_path
        else:
            self.record = False

        self.task = self.config.game.task
        self.camera_stream = camera_stream

        # initialize the output frame and a lock used to ensure thread-safe
        # exchanges of the output frames (useful when multiple browsers/tabs
        # are viewing the stream)
        self.frame_id = 0
        self.output_frame = None

        self.video_stream = None
        self.video_writer = None

        self.tracking_thread = threading.Thread(target=self.tracking)
        self.lock = threading.Lock()

        self.calc = None
        self.psi = 0.0

    @property
    def Sync(self) -> float:
        """
        Compute synchronisation param for given task

        Params
        ------
            None

        Returns
        ------
            synch param between 0 (unsync) and 1 (full sync)
        """
        if self.task == 'manual':
            return self.psi / 10.0
        elif self.task == 'emergence':
            a = 0
            b = 3

            # writing sigmoids in database.db in table 'experiment_parameters'
            write_in_experiment_parameters_sigmoids(a, b, self.experiment_id)

            return 1.0 / (1 + np.exp((self.psi - a) / b))


        else:
            return self.psi

    def set_manual_psi(self, psi: float) -> None:
        if self.task != 'manual':
            if self.task == 'psi':
                if self.calc:
                    self.calc.exit()

            self.task = 'manual'
            self.config.game.task = 'manual'

        self.psi = psi

        logging.info(f"Manually setting psi to {psi}")

    def update_tracking_conf(self, max_players: int) -> None:
        """
        Following a form submission in the front-end, reinitialise tracker with
        new parameters, as well as update config

        Params
        ------
            max_players
                maximum number of objects to be tracked

        Side-effects
        ------
            - reinitialise tracker
        """
        self.config.tracking.max_players = int(max_players)

        self.tracker = EuclideanMultiTracker(self.config.tracking)

        logging.info(f"Updated max_players from Web UI to {max_players} and reinitialised tracker")

    def update_detection_conf(self,
                              min_contour: int, max_contour: int, min_colour, max_colour
                              ) -> None:
        """
        Following a form submission in the front-end, reinitialise detector with
        new parameters, as well as update config

        Params
        ------
            min_contour, max_contour: int
               min and max perimeter of detected blob
            min_colour, max_colour: str
                min and max colours of detected blob in hex, e.g. '#06ff62'

        Side-effects
        ------
            - reinitialise detector
        """
        self.config.detection.min_contour = int(min_contour)
        self.config.detection.max_contour = int(max_contour)
        self.config.detection.min_colour = parse(hex_to_hsv(min_colour))
        self.config.detection.max_colour = parse(hex_to_hsv(max_colour))

        self.detector = Detector(self.config.detection)

        logging.info(f"Updated detector from Web UI and reinitialised:")
        logging.info(f"  min_contour : {min_contour} ")
        logging.info(f"  max_contour : {max_contour} ")
        logging.info(f"  min_colour  : {hex_to_hsv(min_colour)} ")
        logging.info(f"  max_colour  : {hex_to_hsv(max_colour)} ")

    def update_picamera(self,
                        iso: int, shutter_speed: int, saturation: int, awb_mode: str
                        ) -> None:
        """
        Following a form submission in the front-end, update picamera settings
        with new parameters, as well as update config

        Params
        ------
            iso
                sensitivity, min 25, max 800
            shutter_speed
                in milionths of a second
            saturation
                from 1 to 100
            awb_mode
                white balance

        Side-effects
        ------
            - reinitialise tracker
        """
        self.config.camera.iso = int(iso)
        self.config.camera.shutter_speed = int(shutter_speed)
        self.config.camera.saturation = int(saturation)
        self.config.camera.awb_mode = awb_mode

        self.camera.update_settings(self.config)

        logging.info(f"Updated PiCamera settings from Web UI:")
        logging.info(f"  iso           : {iso} ")
        logging.info(f"  shutter_speed : {shutter_speed} ")
        logging.info(f"  saturation    : {saturation} ")
        logging.info(f"  awb_mode      : {awb_mode} ")

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

        bboxes = self.detector.detect_colour(frame)
        self.positions = self.tracker.update(bboxes)

        # writing start coordinates in database.db in table 'trajectories'
        if self.frame_id == 0:
            write_in_trajectories_player_coordinates(self.experiment_id, self.frame_id, bboxes)

        if self.config.tracking.annotate:
            frame = self.detector.draw_annotations(frame, self.positions)

        # acquire the lock, set the output frame, and release the lock
        with self.lock:
            self.output_frame = frame.copy()

        # loop over frames from the video stream and track
        while self.running:
            with self.lock:
                frame = self.video_stream.read()

                if frame is not None:
                    self.frame_id += 1

                if frame is not None and self.record:
                    self.video_writer.write(frame)

            if frame is not None:
                bboxes = self.detector.detect_colour(frame)
                self.positions = self.tracker.update(bboxes)

                if self.task == 'emergence':
                    if len(self.positions) > 1:
                        # compute emergence of positions and update psi
                        X = [[x + w / 2, y + h / 2]
                             for (x, y, w, h) in self.positions]
                        self.psi = self.calc.update_and_compute(np.array(X))

                if self.config.tracking.annotate:
                    if self.task == 'emergence':
                        psi_status = f"Psi: {round(self.psi, 3)}"
                    else:
                        psi_status = ''
                    frame = self.detector.draw_annotations(frame, self.positions,
                                                           extra_text=psi_status)

                # acquire the lock, set the output frame, and release the lock
                with self.lock:
                    self.output_frame = frame.copy()

                # writing to database.db in table 'trajectories'
                write_in_trajectories_player_coordinates(self.experiment_id, self.frame_id, bboxes)
                write_in_trajectories_psis(self.calc.psi, self.calc.psi_filt, self.experiment_id, self.frame_id)

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
        framerate = 12.0
        frametime = 1.0 / framerate
        while self.running:
            # wait until the lock is acquired
            begin = time.time()
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
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encoded_frame) + b'\r\n')
            end = time.time()
            diff = end - begin
            if diff > frametime:
                continue
            else:
                time.sleep(frametime - diff)

    def start(self) -> None:
        """
        Initialises camera stream, tasks and runs tracking process in a thread.
        Ensures only one tracking thread is running at a time.
        """
        # prevent starting tracking thread if one is already running
        if not self.tracking_thread.is_alive():

            # reinitialise tracking_thread in case previous run crashed
            self.tracking_thread = threading.Thread(target=self.tracking)

            self.camera = Camera(self.config.server.CAMERA, self.config.camera, self.camera_stream)
            self.video_stream = self.camera.start()

            self.detector = Detector(self.config.detection)

            self.tracker = EuclideanMultiTracker(self.config.tracking)

            # define video writer to save the stream
            if self.record:
                codec = cv2.VideoWriter_fourcc(*'MJPG')
                date = datetime.datetime.now().strftime('%y-%m-%d_%H%M')
                resolution = unwrap_resolution(self.config.camera.resolution)
                self.video_writer = cv2.VideoWriter(f'{self.record_path}/output_{date}.avi', codec,
                                                    self.config.camera.framerate, resolution)

            # positions of tracked objects
            self.positions = []

            # initialise emergence calculator
            self.psi = 0
            if self.task == 'emergence':
                # TODO: add to config!!
                self.calc = EmergenceCalculator(compute_macro,
                                                use_correction=True, psi_buffer_size=36,
                                                observation_window_size=720)
                logging.info("Initilised EmergenceCalculator")
            elif self.task == '':
                logging.info("No task specified, continuing")

            # writing parameters from emergenceCalculator to database table 'experiment_parameters'
            write_in_experiment_parameters_emergenceCalculator(self.calc.use_correction,
                                                               self.calc.psi_buffer_size,
                                                               self.calc.observation_window_size,
                                                               self.calc.use_local,
                                                               self.experiment_id)

            logging.info("Initialised VideoProcessor with params:")
            logging.info(f"camera type: {self.config.server.CAMERA}")
            logging.info(f"task: {self.task}")
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

        # writing end time of the experiment in database.db in table 'experiment_parameters'
        # TO DO: Does not execute if called after closing video stream due to threading issues
        write_in_experiment_parameters_end_time(self.experiment_id)

        if self.video_stream:
            logging.info('Closing video streamer...')
            self.video_stream.stop()

        if self.record:
            if self.video_writer:
                logging.info('Closing video writer...')
                self.video_writer.release()

        # if self.task == 'emergence':
        #     if self.calc:
        #         self.calc.exit()
