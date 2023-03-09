import signal
from multiprocessing import parent_process
from threading import Lock
from concurrent.futures import ProcessPoolExecutor
from typing import ParamSpec, TypeVar, Callable


class VideoProcessHandle:
    _process_lock = Lock()
    _video_process = ProcessPoolExecutor(max_workers=1)

    _T = TypeVar('_T')
    _P = ParamSpec('_P')

    def exec(self, __fn: Callable[_P, _T], *args, **kwargs) -> _T:
        with self._process_lock:
            if self._video_process is not None:
                return self._video_process.submit(__fn, *args, **kwargs).result()

    def reset_video_process(self):
        with self._process_lock:
            if self._video_process is not None:
                self._video_process.shutdown()
                self.__class__._video_process = ProcessPoolExecutor(max_workers=1)

    _existing_handler = signal.getsignal(signal.SIGINT)

    @staticmethod
    def _cleanup(_signal, _frame):
        with VideoProcessHandle._process_lock:
            if VideoProcessHandle._video_process is not None:
                VideoProcessHandle._video_process.shutdown(cancel_futures=True)
            VideoProcessHandle._existing_handler(_signal, _frame)

    if parent_process() is None:
        signal.signal(signal.SIGINT, _cleanup)
