from typing import Any, cast

import docker
import docker.models
import docker.models.containers
import docker.models.images
import docker.types


class Manager:
    def __init__(self, image: str, client: docker.DockerClient | None = None):
        self.image = image
        self._client = client if client is not None else docker.from_env()

    def auto_run(
        self,
        command: str | list[str] | None = None,
        environment: dict[str, str] | None = None,
        mounts: list[docker.types.Mount] | None = None,
        detach: bool = True,
        **kwargs: Any,
    ) -> bytes | docker.models.containers.Container:
        self.pull()
        return self.run(
            command,
            environment,
            mounts,
            detach,
            **kwargs,
        )

    def run(
        self,
        command: str | list[str] | None = None,
        environment: dict[str, str] | None = None,
        mounts: list[docker.types.Mount] | None = None,
        detach: bool = True,
        **kwargs: dict[str, Any],
    ) -> bytes | docker.models.containers.Container:
        if isinstance(command, list):
            command = " ".join(command)
        if command is not None:
            command = ["/bin/sh", "-c", command]
        return cast(
            bytes | docker.models.containers.Container,
            self._client.containers.run(
                self.image,
                command=command,
                environment=environment,
                mounts=mounts,
                detach=detach,
                stdout=True,
                stderr=True,
                **kwargs,  # type: ignore
            ),
        )

    def pull(self) -> docker.models.images.Image:
        # always pull: if the image is already present and up-to-date,
        # it will be a no-op taking little time
        return self._client.images.pull(self.image)
