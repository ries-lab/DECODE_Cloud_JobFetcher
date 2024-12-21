import os
import time
from multiprocessing import Process
from typing import Any, Generator

import docker
import pytest
import uvicorn


@pytest.fixture(scope="session", autouse=True)
def docker_image() -> str:
    image = "mock_decode"
    version = "test"
    tag = f"{image}:{version}"

    # build docker image from mock_decode
    client = docker.from_env()
    client.images.build(
        path=os.path.join(os.path.dirname(__file__), "..", "..", "mock_decode"),
        buildargs={"VERSION": version},
        tag=tag,
        rm=True,
    )
    return tag


@pytest.fixture(scope="session", autouse=True)
def api_url() -> Generator[str, Any, None]:
    app = "mock_api.app.app:app"
    port = 8000
    host = "0.0.0.0"

    process = Process(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": host, "port": port, "reload": False},
    )
    process.start()
    time.sleep(5)  # wait for the server to start
    yield f"http://localhost:{port}"
    process.terminate()
