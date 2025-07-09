from typing import List

from pydantic import BaseModel

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
    gpus: List[GPUInfo]

def collect() -> SystemInfo: ...
def collect_host() -> HostInfo: ...
def collect_os() -> OSInfo: ...
def collect_sys() -> CPUInfo: ...
def collect_gpus() -> List[GPUInfo]: ...
