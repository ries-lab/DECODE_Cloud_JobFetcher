import itertools
import os
import socket
import time
from pathlib import Path

import docker

from fetcher import api, info, io, status
from fetcher.docker import manager


TIMEOUT = os.getenv("TIMEOUT", 10)
TIMEOUT_MONITOR = os.getenv("TIMEOUT_MONITOR", 2)

path_base = os.getenv("PATH_BASE", "~/temp/decode_cloud/mounts")
path_base = Path(path_base).expanduser()
path_host_base = os.getenv("PATH_HOST_BASE", "~/temp/decode_cloud/mounts")
path_host_base = Path(path_host_base).expanduser()

api_worker = api.worker.API(os.getenv("URL_BASE"), os.getenv("ACCESS_TOKEN"))
worker_info = info.sys.collect()


while True:
    jobs = api_worker.fetch_jobs(
        limit=1,
        hostname=worker_info["host"]["hostname"],
        environment="local",
        cpu_cores=worker_info["sys"]["cores"],
        memory=worker_info["sys"]["memory"],
        gpu_model="3090",  # worker_info["gpu"][0]["model"] if worker_info["gpu"] else None,
        gpu_memory=999999999,  # worker_info["gpu"][0]["memory"] if worker_info["gpu"] else None,
    )

    if len(jobs) >= 1:
        if len(jobs) >= 2:
            raise ValueError(f"Expected only one job, got {len(jobs)}")

        job_id, job = jobs.popitem()
        api_job = api.worker.JobAPI(job_id, api_worker)

        path_job = path_base / job_id

        handler = job.handler
        handler.files_up = [
            io.files.PathAPIUp(path_job / p, path_job, api_job)
            for p_api, p in handler.files_up.items()
        ]
        handler.files_down = [
            io.files.PathAPIDown(path_job / p, p_id, api_job)
            for p, p_id in handler.files_down.items()
        ]

        [p.get() for p in handler.files_down]
        [p.mkdir(exist_ok=True, parents=True) for p in handler.files_up]

        # here we need the paths on the host, we can not do this recursively
        path_mnt = path_host_base / path_job.relative_to(path_base)
        mounts = [
            docker.types.Mount(
                "/data",
                str(path_mnt),
                type="bind",
                read_only=False,
            ),
        ]
        docker_manager = manager.Manager(
            image=job.handler.image_url,
        )
        kwargs_gpu = (
            {
                "device_requests": [
                    docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])
                ],
            }
            if worker_info["gpu"]
            else {}
        )
        container = docker_manager.auto_run(
            command=job.app.cmd,
            environment=job.app.env,
            mounts=mounts,
            detach=True,
            ipc_mode="host",
            **kwargs_gpu,
        )

        # setup pinger
        docker_stat = status.status.DockerStatus(container, ping=api_job.ping)

        # get and keep updating its status
        while True:
            docker_stat.ping()
            if docker_stat.exited:
                print(container.logs())
                break

            time.sleep(TIMEOUT_MONITOR)

        # upload result
        p_upload = itertools.chain(*[p.rglob("*") for p in handler.files_up])
        [p.push() for p in p_upload if p.is_file()]

    # Sleep for a defined interval before checking for the next job
    time.sleep(TIMEOUT)
