import os
import platform
import socket
from typing import TYPE_CHECKING

import psutil
from pydantic import BaseModel

if TYPE_CHECKING:
    import GPUtil
else:
    try:
        import GPUtil
    except ImportError:
        GPUtil = None  # type: ignore


class HostInfo(BaseModel):
    hostname: str


class OSInfo(BaseModel):
    system: str
    release: str
    version: str
    alias: str


class CPUInfo(BaseModel):
    architecture: str
    cores: int
    memory: int


class GPUInfo(BaseModel):
    model: str
    memory: int


class SystemInfo(BaseModel):
    host: HostInfo
    os: OSInfo
    sys: CPUInfo
    gpus: list[GPUInfo]


def collect() -> SystemInfo:
    return SystemInfo(
        host=collect_host(),
        os=collect_os(),
        sys=collect_sys(),
        gpus=collect_gpus(),
    )


def collect_host() -> HostInfo:
    return HostInfo(hostname=socket.gethostname())


def collect_os() -> OSInfo:
    return OSInfo(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        alias=platform.platform(aliased=True),
    )


def collect_sys() -> CPUInfo:
    return CPUInfo(
        architecture=platform.machine(),
        cores=os.cpu_count() or 1,
        memory=psutil.virtual_memory().total >> 20,
    )


def collect_gpus() -> list[GPUInfo]:
    if GPUtil is None:
        return []
    return [
        GPUInfo(
            model=gpu.name,
            memory=int(gpu.memoryTotal),
        )
        for gpu in GPUtil.getGPUs()
    ]
