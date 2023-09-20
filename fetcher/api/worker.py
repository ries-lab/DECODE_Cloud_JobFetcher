from typing import Any, Literal
from pathlib import Path

import requests

from . import model


class API:
    def __init__(self, base_url: str, access_token: str | None = None):
        self.base_url = base_url
        self.access_token = access_token

    @property
    def header(self) -> dict[str, Any] | None:
        if self.access_token is None:
            return None
        return {"Authorization": f"Bearer {self.access_token}"}

    def fetch_jobs(self, **kwargs) -> dict[str, model.Job]:
        response = self._request("GET", "/jobs", params=kwargs)
        return {k: model.Job(**v) for k, v in response.json().items()}

    def get_file(self, file_id: str, path: Path):
        url_getter = self.build_file_url(file_id)
        response = requests.get(url_getter, headers=self.header)
        response.raise_for_status()

        # ToDo: check if response is a URL or a path, currently only URL
        url = response.json()
        response = requests.get(url)  # shall be public
        response.raise_for_status()
        path.write_bytes(response.content)

    def build_file_url(self, file_id: str) -> str:
        return f"{self.base_url}/files_url/{file_id}"

    def _request(self, method: str, endpoint: str, **kwargs):
        url = self.base_url + endpoint
        response = requests.request(method, url, headers=self.header, **kwargs)
        response.raise_for_status()
        return response


def _get_top_level_dir(path) -> str | None:
    if len(path.parts) == 0:
        return None
    elif len(path.parts) == 1 and path.is_file():
        return "."
    return path.parts[0]


class JobAPI:
    _types = {"artifact", "data", "config", "log", "output"}

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
        return f"{self.job_url}/files"

    def ping(
        self,
        status: Literal["running", "stopped", "error"],
        exit_code: int | None,
        body: str,
    ):
        r = requests.put(
            self.status_url,
            params={"status": status},
            json={"exit_code": exit_code, "status_body": body},
            headers=self._base_api.header,
        )
        r.raise_for_status()
        return r

    def get_file(self, file_id: str, path: Path):
        return self._base_api.get_file(file_id, path)

    def put_file(self, path: Path, path_api: str | Path | None, file_type: str):
        f = {"file": (str(path_api), open(path, "rb"))}
        r = requests.post(
            self.file_post_url,
            params={"path": str(path_api), "type": file_type},
            files=f,
            headers=self._base_api.header,
        )
        r.raise_for_status()

    def put_file_native(self, path: Path, path_api: Path):
        if (t := _get_top_level_dir(path_api)) not in self._types:
            raise ValueError(
                f"Top level directory of {path_api} must be one of {self._types}"
            )
        # strip away top level dir
        path_api = path_api.relative_to(t)

        return self.put_file(path, path_api, file_type=t)
