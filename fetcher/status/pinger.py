import abc
import threading
import time
from typing import Any, Callable


class Pinger(abc.ABC):
    @abc.abstractmethod
    def start(self):
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError


class ParallelPinger:
    def __init__(self, ping: Callable[[], Any], timeout: int = 60):
        """Ran parallel to the main thread, requires a stop event to be stopped"""
        self.ping = ping
        self.timeout = timeout
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._ping_loop)

    def _ping_loop(self):
        while not self._stop_event.is_set():
            self.ping()
            time.sleep(self.timeout)

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()


class SerialPinger:
    def __init__(self, ping: Callable[[], bool], timeout: int = 60):
        """Ran in main thread, stops when ping returns False"""
        self.ping = ping
        self.timeout = timeout

    def start(self):
        while True:
            stop = self.ping()
            if stop:
                break
            time.sleep(self.timeout)

    def stop(self):
        pass
