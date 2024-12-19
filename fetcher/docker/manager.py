import docker


class Manager:
    def __init__(self, image: str | None, client: docker.DockerClient | None = None):
        self.image = image
        self._client = client if client is not None else docker.from_env()

    def auto_run(
        self,
        command: str | list[str] | None = None,
        environment: dict[str, str] | None = None,
        mounts: list[docker.types.Mount] | None = None,
        detach: bool = True,
        **kwargs,
    ):
        self.pull()
        return self.run(command, environment, mounts, detach, **kwargs)

    def run(
        self,
        command: str | list[str] | None = None,
        environment: dict[str, str] | None = None,
        mounts: list[docker.types.Mount] | None = None,
        detach: bool = True,
        **kwargs,
    ):
        if isinstance(command, list):
            command = " ".join(command)
        command = ["/bin/sh", "-c", command]
        return self._client.containers.run(
            self.image,
            command=command,
            environment=environment,
            mounts=mounts,
            detach=detach,
            stdout=True,
            stderr=True,
            **kwargs,
        )

    def pull(self):
        # always pull: if the image is already present and up-to-date,
        # it will be a no-op taking little time
        self._client.images.pull(self.image)
