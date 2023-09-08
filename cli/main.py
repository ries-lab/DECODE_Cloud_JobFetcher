import os
import time
from pathlib import Path

import docker
import requests

from fetcher.docker import manager
from fetcher import status

URL_BASE = "http://10.11.39.126:8000"

URL_JOB_GET = os.getenv("URL_JOB_GET", f"{URL_BASE}/job")
URL_JOB_FILES = os.getenv("URL_JOB_STATUS", f"{URL_BASE}/job/$job_id$/file")
URL_JOB_STATUS = os.getenv("URL_JOB_STATUS", f"{URL_BASE}/job/$job_id$/status")
URL_FILES = os.getenv("URL_FILES", f"{URL_BASE}/file/$file_id$")

TIMEOUT = os.getenv("TIMEOUT", 10)
TIMEOUT_MONITOR = os.getenv("TIMEOUT_MONITOR", 2)

PATH_BASE = Path(os.getenv("PATH_BASE", "~/temp/decode_cloud/mounts")).expanduser()


while True:
    # Get job from API
    response = requests.get(URL_JOB_GET)
    data = response.json()

    if data:
        job_id = data["job_id"]

        # download files and save to common space
        paths = data["files"]
        for p, p_id in paths.items():
            p_url = requests.get(URL_FILES.replace("$file_id$", p_id))
            p_url = p_url.json()
            r = requests.get(p_url, allow_redirects=True)

            with (PATH_BASE / p).open("wb") as f:
                f.write(r.content)

        # establish bind mounts
        mounts = [
            docker.types.Mount(
                "/data",
                str(Path("~/temp/decode_cloud/mounts/data").expanduser()),
                type="bind",
                read_only=True,
            ),
            docker.types.Mount(
                "/output",
                str(Path("~/temp/decode_cloud/mounts/output").expanduser()),
                type="bind",
                read_only=False,
            ),
        ]

        docker_manager = manager.Manager(image=f"{data['image']}:{data['image_version']}")
        container = docker_manager.auto_run(
            command=data["command"],
            environment=data["job_env"],
            mounts=mounts,
            detach=True,
        )
        print(f"Started container {container.id} for job {job_id} using {docker_manager.image}")

        # setup pinger
        pinger = status.ping.APIPing(URL_JOB_STATUS.replace("$job_id$", job_id))
        docker_stat = status.status.DockerStatus(container, pinger)

        # get and keep updating its status
        while True:
            docker_stat.ping()
            if docker_stat.exited:
                print(container.logs())
                break

            time.sleep(TIMEOUT_MONITOR)

        # upload result
        path_upload = PATH_BASE / data["path_upload"]
        path_upload = path_upload.glob("*")

        files = [{"file": (str(p), open(p, "rb"))} for p in path_upload]
        [
            requests.post(URL_JOB_FILES.replace("$job_id$", job_id), files=f)
            for f in files
        ]

        # clean up

    # Sleep for a defined interval before checking for the next job
    time.sleep(TIMEOUT)
