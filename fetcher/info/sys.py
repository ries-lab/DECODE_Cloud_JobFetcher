import os
import platform
import socket

import GPUtil
import psutil


def collect() -> dict:
    return {
        "host": collect_host(),
        "os": collect_os(),
        "sys": collect_sys(),
        "gpu": collect_gpu(),
    }


def collect_host() -> dict:
    return {
        "hostname": socket.gethostname(),
    }


def collect_os() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "alias": platform.platform(aliased=True),
    }


def collect_sys() -> dict:
    return {
        "architecture": platform.machine(),
        "cores": os.cpu_count(),
        "memory": psutil.virtual_memory().total,
    }


def collect_gpu() -> list[dict]:
    gpus = GPUtil.getGPUs()
    return [
        {
            "model": g.name,
            "memory": g.memoryTotal * 1e6,
        }
        for g in gpus
    ]
