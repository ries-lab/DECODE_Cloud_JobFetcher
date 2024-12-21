from pydantic import BaseModel

from fetcher.models import FileType


class HardwareSpecs(BaseModel):
    cpu_cores: int | None = None
    memory: int | None = None
    gpu_model: str | None = None
    gpu_archi: str | None = None
    gpu_mem: int | None = None


class MetaSpecs(BaseModel):
    job_id: int
    date_created: str  # iso format

    class Config:
        extra = "allow"


class AppSpecs(BaseModel):
    cmd: list[str] | None = None
    env: dict[str, str] | None = None


class HandlerSpecs(BaseModel):
    image_url: str
    image_name: str | None = None
    image_version: str | None = None
    entrypoint: str | None = None
    files_down: dict[str, str] | None = None
    files_up: dict[FileType, str] | None = None


class JobSpecs(BaseModel):
    app: AppSpecs
    handler: HandlerSpecs
    meta: MetaSpecs
    hardware: HardwareSpecs
