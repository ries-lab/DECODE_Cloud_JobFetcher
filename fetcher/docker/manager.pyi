from typing import Any
import docker
import docker.models
import docker.types

class Manager:
    def __init__(
        self, image: str, client: docker.DockerClient | None = None
    ) -> None: ...
    def auto_run(
        self,
        command: str | list[str] | None = None,
        environment: dict[str, str] | None = None,
        mounts: list[docker.types.Mount] | None = None,
        detach: bool = True,
        **kwargs: Any,
    ) -> bytes | docker.models.containers.Container: ...
    def run(
        self,
        command: str | list[str] | None = None,
        environment: dict[str, str] | None = None,
        mounts: list[docker.types.Mount] | None = None,
        detach: bool = True,
        **kwargs: dict[str, Any],
    ) -> bytes | docker.models.containers.Container: ...
    def pull(self) -> docker.models.images.Image: ...
