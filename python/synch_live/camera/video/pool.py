import signal
import threading
from concurrent.futures import ProcessPoolExecutor

_current_handler = signal.getsignal(signal.SIGINT)


class VideoProcessHandle:
    _process_lock = threading.Lock()
    _video_process = ProcessPoolExecutor(max_workers=1)

    @property
    def process(self) -> ProcessPoolExecutor:
        with self._process_lock:
            return self._video_process

    def reset_video_process(self):
        with self._process_lock:
            self._video_process.shutdown()
            self.__class__._video_process = ProcessPoolExecutor(max_workers=1)

    @staticmethod
    def _shutdown_handler(signum, frame):
        with VideoProcessHandle._process_lock:
            VideoProcessHandle._video_process.shutdown(cancel_futures=True)
            _current_handler(signum, frame)

    signal.signal(signal.SIGINT, _shutdown_handler)
