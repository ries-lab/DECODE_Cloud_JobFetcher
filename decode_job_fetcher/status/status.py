from abc import abstractmethod
from typing import Any, Callable

import docker
import docker.models
import docker.models.containers
from loguru import logger

from ..models import Status as JobStatus


class Status:
    def __init__(
        self,
        ping: Callable[[JobStatus, int | None, str | None], Any],
        *args: list[Any],
        **kwargs: dict[str, Any],
    ):
        """Store/check the status of a job and ping it to an API."""
        self._ping = ping

    @abstractmethod
    def update(self) -> None:
        """Update the status."""
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        """Ping the status. Return True if the status is final."""
        raise NotImplementedError


class ConstantStatus(Status):
    def __init__(
        self,
        status: JobStatus,
        ping: Callable[[JobStatus, int | None, str | None], Any],
    ):
        """A status that never changes.
        Useful e.g. while pre-processing a job, where until the job is started, the status is always "preprocessing".
        :param status: The status to return.
        """
        super().__init__(ping=ping)
        self._status = status

    def update(self) -> None:
        pass

    def ping(self) -> bool:
        self._ping(self._status, None, None)
        return False


class DockerStatus(Status):
    def __init__(
        self,
        container: docker.models.containers.Container,
        ping: Callable[[JobStatus, int | None, str | None], Any],
        update_on_ping: bool = True,
    ):
        """A status that is based on a Docker container.
        When running a Docker container, the status is checked to see if it is running, exited, or exited with an error.
        :param container: The container to check."""
        super().__init__(ping=ping)

        self._container = container
        self._update_on_ping = update_on_ping

    @property
    def exited(self) -> bool:
        return not self._container.attrs["State"]["Running"]

    def update(self) -> None:
        self._container.reload()

    def ping(self) -> bool:
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
