from typing import Any, Optional, Literal
from pydantic import BaseModel

class HardwareSpecs(BaseModel):
    cpu_cores: Optional[int]
    memory: Optional[int]
    gpu_model: Optional[str]
    gpu_archi: Optional[str]
    gpu_mem: Optional[int]

class MetaSpecs(BaseModel):
    job_id: int
    date_created: str

    class Config:
        extra: Literal["allow"]

class AppSpecs(BaseModel):
    cmd: Optional[list[str]]
    env: Optional[dict[str, str]]

class HandlerSpecs(BaseModel):
    image_url: str
    image_name: Optional[str]
    image_version: Optional[str]
    entrypoint: Optional[str]
    files_down: Optional[dict[str, str]]
    files_up: Optional[dict[Any, str]]

class JobSpecs(BaseModel):
    app: AppSpecs
    handler: HandlerSpecs
    meta: MetaSpecs
    hardware: HardwareSpecs
