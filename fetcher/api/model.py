from pathlib import Path

from pydantic import BaseModel


class SpecsHandler(BaseModel):
    image_url: str
    files_down: Path | dict[str, str]
    files_up: Path | dict[str, str]


class SpecsApp(BaseModel):
    cmd: list[str] | None
    env: dict[str, str] | None = None


class SpecsMeta(BaseModel):
    class Config:
        extra = "allow"


class SpecsHardware(BaseModel):
    cpu_cores: int | None = None
    memory: int | None = None
    gpu_model: str | None = None
    gpu_archi: str | None = None
    gpu_mem: int | None = None


class Job(BaseModel):
    app: SpecsApp
    handler: SpecsHandler
    meta: SpecsMeta
    hardware: SpecsHardware
