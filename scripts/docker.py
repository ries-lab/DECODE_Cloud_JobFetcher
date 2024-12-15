import os
from pathlib import Path

import docker
import dotenv
import GPUtil
import toml


def _get_client() -> docker.DockerClient:
    return docker.from_env()


def _get_package_name() -> str:
    with open("pyproject.toml", "r") as file:
        pyproject_data = toml.load(file)
    pkg_name = pyproject_data["tool"]["poetry"]["name"]
    assert isinstance(pkg_name, str)
    return pkg_name


def _get_python_version() -> str:
    with open("pyproject.toml", "r") as file:
        pyproject_data = toml.load(file)
    python_version = pyproject_data["tool"]["poetry"]["dependencies"]["python"]
    assert isinstance(python_version, str)
    return python_version


def _get_git_branch() -> str:
    return os.popen("git branch --show-current").read().strip()


def build() -> None:
    """
    Builds a Docker image for the current branch.
    """
    client = _get_client()
    client.images.build(
        path=os.path.join(os.path.dirname(__file__), ".."),
        tag=f"{_get_package_name()}:{_get_git_branch()}",
        nocache=True,
        rm=True,
        pull=True,
        buildargs={"PYTHON_VERSION": _get_python_version()},
    )


def run() -> None:
    """
    Runs a Docker container for the current branch.
    """
    client = _get_client()
    path_base = os.environ.get("PATH_BASE", "/data")
    path_host_base = os.environ.get(
        "PATH_HOST_BASE", os.path.join(os.path.dirname(__file__), "..", "data")
    )
    os.makedirs(path_host_base, exist_ok=True)
    client.containers.run(
        image=f"{_get_package_name()}:{_get_git_branch()}",
        environment={k: v for k, v in dotenv.dotenv_values().items() if v is not None},
        volumes={
            str(Path.home() / ".aws" / "credentials"): {
                "bind": "/home/app/.aws/credentials",
                "mode": "ro",
            },
            "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
            path_host_base: {"bind": path_base, "mode": "rw"},
        },
        device_requests=[
            docker.types.DeviceRequest(
                device_ids=[gpu.uuid for gpu in GPUtil.getGPUs()],
                capabilities=[["gpu"]],
            )
        ],
        extra_hosts={"host.docker.internal": "host-gateway"},
        auto_remove=True,
    )


def stop() -> None:
    """
    Stops and deletes all Docker containers for this package.
    """
    client = _get_client()
    for container in client.containers.list(ignore_removed=True):
        if container.attrs["Config"]["Image"].startswith(_get_package_name() + ":"):
            container.remove(force=True)


def cleanup() -> None:
    """
    Removes all Docker images for this package, prune dangling images.
    Deletes all containers for this package.
    """
    stop()
    client = _get_client()
    for image in client.images.list(name=_get_package_name()):
        client.images.remove(image.id, force=True)
    client.images.prune(filters={"dangling": True})
