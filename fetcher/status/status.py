from abc import abstractmethod
from typing import Callable

from loguru import logger


class Status:
    def __init__(self, ping: Callable):
        self._ping = ping

    @abstractmethod
    def update(self):
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        """Ping the status. Return True if the status is final."""
        raise NotImplementedError


class ConstantStatus(Status):
    def __init__(self, status: str, ping: Callable):
        super().__init__(ping=ping)
        self._status = status

    def update(self):
        pass

    def ping(self):
        self._ping(self._status, None, None)
        return False


class DockerStatus(Status):
    def __init__(self, container, ping: Callable, update_on_ping: bool = True):
        super().__init__(ping=ping)

        self._container = container
        self._update_on_ping = update_on_ping

    @property
    def exited(self):
        return not self._container.attrs["State"]["Running"]

    def update(self):
        self._container.reload()

    def ping(self):
        if self._update_on_ping:
            self.update()
        logger.debug(f"Container state: {self._container.attrs['State']}")

        match self._container.attrs["State"]:
            case {"Status": "running"}:
                self._ping("running", None, None)
            case {"Status": "exited", "ExitCode": 0}:
                self._ping("postprocessing", 0, None)
            case {"Status": "exited", "ExitCode": exit_code, "Error": err_info}:
                logger.error(
                    f"Container exited with error code {exit_code}: {err_info}"
                )
                self._ping("error", exit_code, err_info)
            case _:
                raise ValueError

        return self.exited
