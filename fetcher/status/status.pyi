from typing import Any, Callable
from abc import abstractmethod
import docker

class Status:
    def __init__(
        self,
        ping: Callable[[Any, int | None, str | None], Any],
        *args: list[Any],
        **kwargs: dict[str, Any]
    ): ...
    @abstractmethod
    def update(self) -> None: ...
    @abstractmethod
    def ping(self) -> bool: ...

class ConstantStatus(Status):
    def __init__(
        self,
        status: Any,
        ping: Callable[[Any, int | None, str | None], Any],
    ): ...
    def update(self) -> None: ...
    def ping(self) -> bool: ...

class DockerStatus(Status):
    def __init__(
        self,
        container: docker.models.containers.Container,
        ping: Callable[[Any, int | None, str | None], Any],
        update_on_ping: bool = True,
    ): ...
    @property
    def exited(self) -> bool: ...
    def update(self) -> None: ...
    def ping(self) -> bool: ...
