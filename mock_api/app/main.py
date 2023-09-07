from typing import Literal

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

app = FastAPI()


class Job(BaseModel):
    job_id: str
    image: str
    image_version: str
    files: dict[str, str]
    path_upload: str


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
        case _:
            print(file_id)
            raise ValueError(f"Unknown file_id {file_id}")

    return url


@app.get("/job")
async def job_get() -> Job:
    return Job(
        job_id="a6",
        image="mock_decode",
        image_version="0.0.2",
        files={
            "config/music.mp3": "music",  # path / file_id
            "config/video.mp3": "video",
        },
        path_upload="output/",
    )


@app.post("/job/{job_id}/file")
async def job_file_post(job_id: str, file: UploadFile = File(...)):
    print(f"Uploaded file for {job_id} with file {file.filename}")
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
