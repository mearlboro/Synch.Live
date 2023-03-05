import logging
import os
from concurrent.futures import ProcessPoolExecutor
from types import SimpleNamespace
from typing import Generator

from flask import current_app
from imutils.video import VideoStream
from yaml import safe_load

from synch_live.camera.tools.config import parse
from . import VideoProcessor
from ..tools.colour import hsv_to_hex

video_process = ProcessPoolExecutor(max_workers=1)


class VideoProcessorServer:
    processor: VideoProcessor = None

    @staticmethod
    def __init__(config_path: str):
        if VideoProcessorServer.processor is not None:
            return
        if config_path is None:
            raise NameError
        if not os.path.exists(config_path):
            raise FileNotFoundError
        with open(config_path, 'r') as handle:
            config = parse(safe_load(handle))
            config.conf_path = config_path
            # NOTE: to use /dev/video* devices, you must launch in the main process
            #       so we create the camera stream here
            camera_number = config.server.CAMERA
            camera_stream = None
            if camera_number is not None and type(camera_number) == int:
                logging.info(f"Opening Camera {camera_number}")
                camera_stream = VideoStream(int(camera_number), framerate=config.camera.framerate)
            VideoProcessorServer.processor = VideoProcessor(config, camera_stream)

    def __del__(self):
        if VideoProcessorServer.processor is None:
            return
        VideoProcessorServer.stop()

    @staticmethod
    def next_frame() -> bytes | StopIteration:
        try:
            return next(VideoProcessorServer.processor.generate_frame())
        except StopIteration as e:
            return e

    @staticmethod
    def start():
        if not VideoProcessorServer.processor.running:
            VideoProcessorServer.processor.start()

    @staticmethod
    def stop():
        if VideoProcessorServer.processor.running:
            VideoProcessorServer.processor.stop()

    @staticmethod
    def get_config() -> SimpleNamespace:
        return VideoProcessorServer.processor.config

    @staticmethod
    def set_config(config: SimpleNamespace):
        VideoProcessorServer.processor.update_tracking_conf(config.tracking.max_players)
        VideoProcessorServer.processor.update_detection_conf(config.detection.min_contour, config.detection.max_contour,
                                                             hsv_to_hex(config.detection.min_colour.__dict__),
                                                             hsv_to_hex(config.detection.max_colour.__dict__))
        if VideoProcessorServer.get_config().server.CAMERA == 'pi':
            VideoProcessorServer.processor.update_picamera(config.iso, config.shutter_speed, config.saturation,
                                                           config.awb_mode)

    @staticmethod
    def get_running() -> bool:
        return VideoProcessorServer.processor.running

    @staticmethod
    def get_sync() -> float:
        if VideoProcessorServer.processor.running:
            return VideoProcessorServer.processor.Sync

    @staticmethod
    def get_task() -> str:
        return VideoProcessorServer.processor.task

    @staticmethod
    def set_task(task: str):
        VideoProcessorServer.processor.task = task

    @staticmethod
    def get_psi() -> float:
        return VideoProcessorServer.processor.psi

    @staticmethod
    def set_psi(psi: float):
        VideoProcessorServer.processor.set_manual_psi(psi)


class VideoProcessorClient:
    def __init__(self):
        self.process = video_process

    def start(self):
        self.process.submit(VideoProcessorServer.start).result()

    def stop(self):
        global video_process
        self.process.submit(VideoProcessorServer.stop).result()
        self.process.shutdown()
        video_process = ProcessPoolExecutor(max_workers=1)
        self.process = video_process
        self.process.submit(VideoProcessorServer, current_app.config['VIDEO_CONFIG']).result()

    def generate_frame(self) -> Generator[bytes, None, None]:
        while True:
            res = self.process.submit(VideoProcessorServer.next_frame).result()
            if res is StopIteration:
                break
            yield res

    @property
    def running(self) -> bool:
        return self.process.submit(VideoProcessorServer.get_running).result()

    @property
    def sync(self) -> float:
        return self.process.submit(VideoProcessorServer.get_sync).result()

    @property
    def config(self) -> SimpleNamespace:
        return self.process.submit(VideoProcessorServer.get_config).result()

    @config.setter
    def config(self, config: SimpleNamespace):
        self.process.submit(VideoProcessorServer.set_config, config).result()

    @property
    def psi(self) -> float:
        return self.process.submit(VideoProcessorServer.get_psi).result()

    @psi.setter
    def psi(self, psi: float):
        self.process.submit(VideoProcessorServer.set_psi, psi).result()

    @property
    def task(self) -> float:
        return self.process.submit(VideoProcessorServer.get_task).result()

    @task.setter
    def task(self, task: str):
        self.process.submit(VideoProcessorServer.set_task, task).result()
