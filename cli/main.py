import os
import socket
import time
from pathlib import Path

import docker
import requests

from fetcher.docker import manager
from fetcher import info, io, status

host_name = socket.gethostname()
try:
    host_ip = socket.gethostbyname(host_name)
except socket.gaierror:
    host_ip = "localhost"

URL_BASE = os.getenv("URL_BASE", "http://host.docker.internal:8000")
url_job_get = f"{URL_BASE}/job"
url_job_file = f"{URL_BASE}/job/$job_id$/file"
url_job_status = f"{URL_BASE}/job/$job_id$/status"
url_files = f"{URL_BASE}/file_url/$file_id$"

TIMEOUT = os.getenv("TIMEOUT", 10)
TIMEOUT_MONITOR = os.getenv("TIMEOUT_MONITOR", 2)

PATH_BASE = Path(os.getenv("PATH_BASE", "~/temp/decode_cloud/mounts")).expanduser()
path_host_base = Path(os.getenv("PATH_HOST_BASE", "~/temp/decode_cloud/mounts")).expanduser()

worker_info = info.sys.collect()


while True:
    # Get job from API
    response = requests.get(
        url_job_get,
        params={
            "limit": 1,
            "hostname": host_name,
            "env": "local",
            "cpu_cores": worker_info["sys"]["cores"],
            "memory": worker_info["sys"]["memory"],
            "gpu_model": worker_info["gpu"][0]["model"] if worker_info["gpu"] else None,
            "gpu_memory": worker_info["gpu"][0]["memory"]
            if worker_info["gpu"]
            else None,
        },
    )
    response.raise_for_status()
    data = response.json()

    if data is not None:
        data = data[0]
        job_id = data["job_id"]

        # establish temporary directory for the job
        exist_ok = True  # debugging

        path_job = PATH_BASE / job_id
        path_job.mkdir(parents=False, exist_ok=exist_ok)

        path_data = path_job / "data"
        path_data.mkdir(parents=False, exist_ok=exist_ok)
        path_out = path_job / "output"
        path_out.mkdir(parents=False, exist_ok=exist_ok)

        # download files and save to common space
        downloader = io.files.APIDownloader(path_job)
        paths = data["files"]
        for p, p_id in paths.items():
            if Path(p).is_absolute():
                raise ValueError(f"Absolute paths are not allowed: {p}")
            p = path_job / p
            p.parent.mkdir(parents=True, exist_ok=True)

            # get URL for file by its ID
            r = requests.get(url_files.replace("$file_id$", p_id))
            r.raise_for_status()
            url = r.json()

            downloader.get(url, p)
            # print("Downloaded file", url, "to", p)

        # here we need the paths on the host, we can not do this recursively
        path_mnt = path_host_base / path_job.relative_to(PATH_BASE)
        print("Mountpoint for child container:", path_mnt)
        mounts = [
            docker.types.Mount(
                "/data",
                str(path_mnt),
                type="bind",
                read_only=False,
            ),
        ]
        docker_manager = manager.Manager(
            image=f"{data['image']}:{data['image_version']}"
        )
        kwargs_gpu = {
            "device_requests": [
                docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])
            ],
        } if worker_info["gpu"] else {}
        container = docker_manager.auto_run(
            command=data["command"],
            environment=data["job_env"],
            mounts=mounts,
            detach=True,
            ipc_mode="host",
            **kwargs_gpu,
        )
        # print(
        #     f"Started container {container.id} for job {job_id} using {docker_manager.image}"
        # )

        # setup pinger
        pinger = status.ping.APIPing(url_job_status.replace("$job_id$", job_id))
        docker_stat = status.status.DockerStatus(container, pinger)

        # get and keep updating its status
        while True:
            docker_stat.ping()
            if docker_stat.exited:
                print(container.logs())
                break

            time.sleep(TIMEOUT_MONITOR)

        # upload result
        uploader = io.files.APIUploader(url_job_file.replace("$job_id$", job_id))
        paths_upload = path_out.glob("*")
        [uploader.put(p) for p in paths_upload if p.is_file()]

    # Sleep for a defined interval before checking for the next job
    time.sleep(TIMEOUT)
