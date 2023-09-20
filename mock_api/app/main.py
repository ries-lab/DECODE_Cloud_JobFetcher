from pathlib import Path
from typing import Literal, Any

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/file_url/{file_id}")
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

    return url


class SpecsHandler(BaseModel):
    image_url: str
    files_down: dict[str, str]
    files_up: dict[str, str]
    aws_job_def: Any


class SpecsApp(BaseModel):
    cmd: list[str] | None
    env: dict[str, str] | None = None


class SpecsMeta(BaseModel):
    class Config:
        extra = "allow"


class Job(BaseModel):
    app: SpecsApp
    handler: SpecsHandler
    meta: SpecsMeta

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
                    "Paths.logging=/data/log"
                ],
                "env": {}
            },
            "handler": {
                "image_url": "public.ecr.aws/d2r7a3u1/decode:dev_multiphot_tar",
                "aws_job_def": "decode_train_latest",
                "files_down": {
                    "config/config.yaml": "config_file_id",
                    "data/beads.mat": "beads_file_id",
                    "data/trafo.mat": "trafo_file_id"
                },
                "files_up": {
                    "log": "log",
                    "artifact": "model"
                }
            },
            "meta": {
                "job_id": 9,
                "date_created": "2023-09-20T14:14:37.596024"
            }
        }
    }
    # return {
    #     "a6": Job(
    #         app=SpecsApp(
    #             cmd=[
    #                 # fmt: off
    #                 # "python", "-m", "cli.train",
    #                 "--config-dir", "/data/config/",
    #                 "--config-name", "config",
    #                 "Trainer.max_epochs=1",
    #                 # fmt: on
    #             ]
    #         ),
    #         handler=SpecsHandler(
    #             image_url="decode:dev_multiphot_tar",
    #             files_down={
    #                 "config/config.yaml": "config_a6",
    #                 "data/beads.mat": "beads_a6",
    #                 "data/trafo.mat": "trafo_a6",
    #             },
    #             files_up={"artifact": "output/", "log": "log/"},
    #         ),
    #         meta=SpecsMeta(date_created="2021-08-01T12:00:00+00:00"),
    #     )
    # }
    return {
        "mock_a6": Job(
            app=SpecsApp(
                cmd=None
            ),
            handler=SpecsHandler(
                image_url="mock_decode:0.0.6",
                files_down={
                    "config/config.yaml": "config_a6",
                    "data/beads.mat": "beads_a6",
                    "data/trafo.mat": "trafo_a6",
                },
                files_up={"artifact": "artifact/", "log": "log/", "output": "output/"},
            ),
            meta=SpecsMeta(date_created="2021-08-01T12:00:00+00:00"),
        )
    }


@app.post("/jobs/{job_id}/file")
async def job_file_post(
    job_id: str,
    path: str,
    type: Literal["artifact", "log", "output"],
    file: UploadFile = File(...),
):
    # put file
    print(
        f"Would have uploaded file {file.filename} of type {type} for {job_id}; "
        f"dumping it to {path}"
    )
    return {"filename": file.filename}


@app.get("/jobs/{job_id}/status")
async def job_status_get(job_id):
    return {"message": f"The job with ID {job_id}."}


class StatusBody(BaseModel):
    status_body: str | None


@app.put("/jobs/{job_id}/status")
async def job_status_put(
    job_id: str,
    status: Literal["running", "stopped", "error"],
    status_body: StatusBody | None = None,
):
    return {
        "job_id": job_id,
        "status": status,
        "status_body": status_body.status_body,
    }
