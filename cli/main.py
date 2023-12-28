import itertools
import os
import time
from fastapi import HTTPException
from pathlib import Path

import docker
import dotenv
from loguru import logger

from fetcher import api, info, io, status
from fetcher.docker import manager

dotenv.load_dotenv(override=True)

TIMEOUT = os.getenv("TIMEOUT", 10)
TIMEOUT_MONITOR = os.getenv("TIMEOUT_MONITOR", 2)

path_base = os.getenv("PATH_BASE", "~/temp/decode_cloud/mounts")
path_base = Path(path_base).expanduser()
path_host_base = os.getenv("PATH_HOST_BASE")

# ToDo: use AccessTokenAuth
api_worker = api.worker.API(
    os.getenv("API_URL"), api.token.AccessTokenFixed(os.getenv("ACCESS_TOKEN"))
)
worker_info = info.sys.collect()


while True:
    try:
        container = None
        jobs = api_worker.fetch_jobs(
            limit=1,
            cpu_cores=worker_info["sys"]["cores"],
            memory=worker_info["sys"]["memory"],
            gpu_model=worker_info["gpu"][0]["model"] if worker_info["gpu"] else None,
            gpu_memory=worker_info["gpu"][0]["memory"] if worker_info["gpu"] else None,
        )

        if len(jobs) == 0:
            logger.info(f"No job found. Sleeping for {TIMEOUT} seconds.")
            time.sleep(TIMEOUT)
            continue

        if len(jobs) >= 2:
            raise ValueError(f"Expected only one job, got {len(jobs)}")

        job_id, job = jobs.popitem()
        api_job = api.worker.JobAPI(job_id, api_worker)

        pinger_pre = status.pinger.SerialPinger(
            ping=status.status.ConstantStatus(
                status="preprocessing", ping=api_job.ping
            ).ping,
            timeout=TIMEOUT_MONITOR,
        )
        pinger_pre.start()

        path_job = path_base / job_id

        handler = job.handler
        handler.files_up = [
            io.files.PathAPIUp(path_job / p, f_type, path_job, api_job)
            for f_type, p in handler.files_up.items()
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

        pinger_pre.stop()

        # get and keep updating its status
        pinger_run = status.pinger.SerialPinger(
            ping=status.status.DockerStatus(container, ping=api_job.ping).ping,
            timeout=TIMEOUT_MONITOR,
        )
        pinger_run.start()
        pinger_run.stop()
        print(container.logs())

        # upload result
        pinger_post = status.pinger.SerialPinger(
            ping=status.status.ConstantStatus(
                status="postprocessing", ping=api_job.ping
            ).ping,
            timeout=TIMEOUT_MONITOR,
        )
        pinger_post.start()
        p_upload = itertools.chain(*[p.rglob("*") for p in handler.files_up])
        [p.push() for p in p_upload if p.is_file()]
        pinger_post.stop()

    except HTTPException as e:
        if e.status_code == 404:
            logger.warning(
                f"Job {job_id} not found; it was probably deleted by the user."
            )
            if container:
                container.kill()
            continue
