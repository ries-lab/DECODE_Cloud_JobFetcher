import os
from pathlib import Path
from typing import Any, Literal

from fetcher.session import session

from . import model, token


class API:
    def __init__(self, base_url: str, access_token: token.AccessToken | None = None):
        self.base_url = base_url
        self.access_token = access_token

    @property
    def header(self) -> dict[str, Any] | None:
        if self.access_token is None:
            return None
        return {"Authorization": f"Bearer {self.access_token.access_token}"}

    def fetch_jobs(self, **kwargs) -> dict[str, model.Job]:
        response = self._request("GET", "/jobs", params=kwargs)
        return {k: model.Job(**v) for k, v in response.json().items()}

    def get_file(self, file_id: str, path: Path):
        url_getter = self.build_file_url(file_id)
        response = session.get(url_getter, headers=self.header)

        # ToDo: check if response is a URL or a path, currently only URL
        response = response.json()
        response = session.request(**response)  # may contain authorization header
        path.write_bytes(response.content)

    def build_file_url(self, file_id: str) -> str:
        return f"{self.base_url}/files/{file_id}/url"

    def _request(self, method: str, endpoint: str, **kwargs):
        url = self.base_url + endpoint
        response = session.request(method, url, headers=self.header, **kwargs)
        return response


def _get_top_level_dir(path) -> str | None:
    if len(path.parts) == 0:
        return None
    elif len(path.parts) == 1 and path.is_file():
        return "."
    return path.parts[0]


class JobAPI:
    def __init__(self, job_id: str, base_api: API):
        self.job_id = job_id
        self._base_api = base_api

    @property
    def job_url(self) -> str:
        return f"{self._base_api.base_url}/jobs/{self.job_id}"

    @property
    def status_url(self) -> str:
        return f"{self.job_url}/status"

    @property
    def file_post_url(self) -> str:
        return f"{self.job_url}/files/url"

    def ping(
        self,
        status: Literal[
            "preprocessing", "running", "postprocessing", "finished", "error"
        ],
        exit_code: int | None,
        body: str | None,
    ):
        runtime_details = None
        if exit_code is not None:
            runtime_details = f"exit_code: {exit_code} "
        if body is not None:
            runtime_details = (runtime_details or "") + body
        r = session.put(
            self.status_url,
            params={"status": status, "runtime_details": body},
            headers=self._base_api.header,
        )
        return r

    def get_file(self, file_id: str, path: Path):
        return self._base_api.get_file(file_id, path)

    def put_file(self, path: Path, path_api: str | Path | None, file_type: str):
        # Get file upload pre-signed URL
        response = session.post(
            self.file_post_url,
            params={"base_path": str(os.path.dirname(path_api)), "type": file_type},
            headers=self._base_api.header,
        )

        # Upload file
        response = response.json()
        f = {"file": (str(os.path.split(path_api)[-1]), open(path, "rb"))}
        response = session.request(**response, files=f)

    def put_file_native(
        self, path: Path, f_type: Literal["artifact", "output", "log"], path_api: Path
    ):
        return self.put_file(path, path_api, file_type=f_type)
