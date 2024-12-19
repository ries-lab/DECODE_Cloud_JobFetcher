from typing import Any, Literal

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/files/{file_id}/url")
async def file_get(file_id) -> str:
    # return presigned public URL
    match file_id:
        case "config_file_id":
            url = "https://oc.embl.de/index.php/s/Vt8Tz9c4YlHikOr/download"
        case "beads_file_id":
            url = "https://oc.embl.de/index.php/s/0FIg3YfBSooZiMI/download"
        case "trafo_file_id":
            url = "https://oc.embl.de/index.php/s/mc9oilE0d6fcN52/download"
        case "MB5":
            url = "http://212.183.159.230/5MB.zip"
        case "MB10":
            url = "http://212.183.159.230/10MB.zip"
        case _:
            print(file_id)
            raise ValueError(f"Unknown file_id {file_id}")

    return {"url": url, "method": "get"}


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
    files_up: dict[Literal["output", "log", "artifact"], str] | None = None


class JobSpecs(BaseModel):
    app: AppSpecs
    handler: HandlerSpecs
    meta: MetaSpecs
    hardware: HardwareSpecs

    class Config:
        orm_mode = True


@app.get("/jobs")
async def job_get(
    hostname: str,
    cpu_cores: int,
    memory: int,
    env: str | None = None,
    gpu_model: str | None = None,
    gpu_archi: str | None = None,
    gpu_mem: int | None = None,
    groups: list[str] | None = None,
    limit: int = 1,
    older_than: int | None = None,
) -> dict[str, Any]:
    return {
        "5": {
            "app": {
                "cmd": [
                    "--config-dir=/data/config",
                    "--config-name=config",
                    "Paths.experiment=/data/model",
                    "Paths.logging=/data/log",
                ],
                "env": {},
            },
            "handler": {
                "image_url": "public.ecr.aws/d2r7a3u1/decode:dev_multiphot_tar",
                "aws_job_def": "decode_train_latest",
                "files_down": {
                    "config/config.yaml": "config_file_id",
                    "data/beads.mat": "beads_file_id",
                    "data/trafo.mat": "trafo_file_id",
                },
                "files_up": {"log": "log", "artifact": "model"},
            },
            "meta": {"job_id": 9, "date_created": "2023-09-20T14:14:37.596024"},
            "hardware": {},
        }
    }
    # return {
    #     "a6": JobSpecs(
    #         app=AppSpecs(
    #             cmd=[
    #                 # fmt: off
    #                 # "python", "-m", "cli.train",
    #                 "--config-dir", "/data/config/",
    #                 "--config-name", "config",
    #                 "Trainer.max_epochs=1",
    #                 # fmt: on
    #             ]
    #         ),
    #         handler=HandlerSpecs(
    #             image_url="decode:dev_multiphot_tar",
    #             files_down={
    #                 "config/config.yaml": "config_a6",
    #                 "data/beads.mat": "beads_a6",
    #                 "data/trafo.mat": "trafo_a6",
    #             },
    #             files_up={"artifact": "output/", "log": "log/"},
    #         ),
    #         meta=MetaSpecs(date_created="2021-08-01T12:00:00+00:00"),
    #     )
    # }
    # return {
    #     "mock_a6": JobSpecs(
    #         app=AppSpecs(
    #             cmd=None
    #         ),
    #         handler=HandlerSpecs(
    #             image_url="mock_decode:0.0.6",
    #             files_down={
    #                 "config/config.yaml": "config_a6",
    #                 "data/beads.mat": "beads_a6",
    #                 "data/trafo.mat": "trafo_a6",
    #             },
    #             files_up={"artifact": "artifact/", "log": "log/", "output": "output/"},
    #         ),
    #         meta=MetaSpecs(date_created="2021-08-01T12:00:00+00:00"),
    #     )
    # }


@app.post("/jobs/{job_id}/files/url")
async def job_file_post(
    job_id: str,
    type: Literal["artifact", "log", "output"],
    base_path: str = "",
    file: UploadFile = File(...),
):
    return {"url": "https://fake_url.com", "method": "put", "data": {}}


@app.get("/jobs/{job_id}/status")
async def job_status_get(job_id):
    return {"message": f"The job with ID {job_id}."}


@app.put("/jobs/{job_id}/status")
async def job_status_put(
    job_id: str,
    status: Literal["preprocessing", "running", "postprocessing", "finished", "error"],
    runtime_details: str | None = None,
):
    return {
        "job_id": job_id,
        "status": status,
        "runtime_details": runtime_details,
    }
