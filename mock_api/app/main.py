from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/file/{file_id}")
async def file_get(file_id) -> str:
    # return presigned public URL
    match file_id:
        case "music":
            url = "http://212.183.159.230/5MB.zip"
        case "video":
            url = "http://212.183.159.230/10MB.zip"
        case "decode_file":
            url = "https://oc.embl.de/index.php/s/GzSbmU7pheHEdC0/download"
        case _:
            print(file_id)
            raise ValueError(f"Unknown file_id {file_id}")

    return url


class Job(BaseModel):
    job_id: str
    image: str
    image_version: str
    command: str | list[str] | None
    job_env: dict[str, str] | None
    files: dict[str, str]
    path_upload: str


@app.get("/job")
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
) -> list[Job]:
    if "gpu_model" is not None:
        return [
            Job(
                job_id="a6",
                image="decode",
                image_version="dev_multiphot_tar",
                command=[
                    # fmt: off
                    "python", "-m", "cli.train",
                    "--config-dir", "/data/config/",
                    "--config-name", "config.yaml"
                    "Paths.calibration=/data/data/beads.mat",
                    "Paths.trafo=/data/data/trafo.mat",
                    "Paths.experiment=/output/",
                    "Paths.data=/output/"
                    # fmt: on
                ],
                job_env={"JOB_ID": "a6"},
                files={
                    "config/config.yaml": "https://oc.embl.de/index.php/s/Vt8Tz9c4YlHikOr/download",
                    "data/trafo.mat": "https://oc.embl.de/index.php/s/mc9oilE0d6fcN52/download",
                    "data/beads.mat": "https://oc.embl.de/index.php/s/0FIg3YfBSooZiMI/download",
                },
                path_upload="/output/",
            )
        ]
    else:
        raise ValueError("No GPU available")


@app.post("/job/{job_id}/file")
async def job_file_post(job_id: str, file: UploadFile = File(...)):
    # put file
    p = Path("~/temp/decode_cloud/api").expanduser() / Path(file.filename).name

    print(f"Uploaded file for {job_id} with file {file.filename}, dumping it to {p}")
    with p.open("wb") as f:
        f.write(file.file.read())

    return {"filename": file.filename}


@app.get("/job/{job_id}/status")
async def job_status_get(job_id):
    return {"message": f"The job with ID {job_id}."}


class StatusBody(BaseModel):
    status_body: str | None


@app.put("/job/{job_id}/status")
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
