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
        **kwargs
    ):
        self.pull()
        return self.run(command, environment, mounts, detach, **kwargs)

    def run(
        self,
        command: str | list[str] | None = None,
        environment: dict[str, str] | None = None,
        mounts: list[docker.types.Mount] | None = None,
        detach: bool = True,
        **kwargs
    ):
        return self._client.containers.run(
            self.image,
            command=command,
            environment=environment,
            mounts=mounts,
            detach=detach,
            **kwargs,
        )

    def pull(self):
        try:
            self._client.images.get(self.image)
        except docker.errors.ImageNotFound:
            self._client.images.pull(self.image)
