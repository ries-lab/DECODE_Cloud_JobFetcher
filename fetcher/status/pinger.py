import abc
import threading
import time
from typing import Callable


class Pinger(abc.ABC):
    @abc.abstractmethod
    def __init__(self, ping: Callable[[], bool], timeout: int | float = 60):
        raise NotImplementedError

    @abc.abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> None:
        raise NotImplementedError


class ParallelPinger:
    def __init__(self, ping: Callable[[], bool], timeout: int | float = 60):
        """Ran parallel to the main thread, requires a stop event to be stopped"""
        self.ping = ping
        self.timeout = timeout
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._ping_loop)

    def _ping_loop(self) -> None:
        while not self._stop_event.is_set():
            self.ping()
            time.sleep(self.timeout)

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join()


class SerialPinger:
    def __init__(self, ping: Callable[[], bool], timeout: int | float = 60):
        """Ran in main thread, stops when ping returns False"""
        self.ping = ping
        self.timeout = timeout

    def start(self) -> None:
        while True:
            stop = self.ping()
            if stop:
                break
            time.sleep(self.timeout)

    def stop(self) -> None:
        pass
