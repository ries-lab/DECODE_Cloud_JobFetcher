import os
from pathlib import Path
from typing import Any

import requests

from fetcher.api import model, token
from fetcher.models import FileType, Status
from fetcher.session import session


class API:
    def __init__(self, base_url: str, access_token: token.AccessToken | None = None):
        self.base_url = base_url
        self.access_token = access_token

    @property
    def header(self) -> dict[str, str] | None:
        if self.access_token is None:
            return None
        return {"Authorization": f"Bearer {self.access_token.access_token}"}

    def fetch_jobs(self, **kwargs: Any) -> dict[str, model.JobSpecs]:
        response = self._request("GET", "/jobs", params=kwargs)
        return {k: model.JobSpecs(**v) for k, v in response.json().items()}

    def get_file(self, file_id: str, path: Path) -> requests.Response:
        url_getter = self.build_file_url(file_id)
        response = session.get(url_getter, headers=self.header)

        # ToDo: check if response is a URL or a path, currently only URL
        request_kwargs = response.json()
        response = session.request(**request_kwargs)  # may contain authorization header
        path.write_bytes(response.content)
        return response

    def build_file_url(self, file_id: str) -> str:
        return f"{self.base_url}/files/{file_id}/url"

    def _request(
        self, method: str, endpoint: str, **kwargs: dict[str, Any]
    ) -> requests.Response:
        url = self.base_url + endpoint
        response = session.request(
            method=method,
            url=url,
            headers=self.header,
            **kwargs,  # type: ignore
        )
        return response


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
        status: Status,
        exit_code: int | None,
        body: str | None,
    ) -> requests.Response:
        runtime_details = None
        if exit_code is not None:
            runtime_details = f"exit_code: {exit_code} "
        if body is not None:
            runtime_details = (runtime_details or "") + body
        return session.put(
            self.status_url,
            params={"status": status, "runtime_details": body},
            headers=self._base_api.header,
        )

    def get_file(self, file_id: str, path: Path) -> requests.Response:
        return self._base_api.get_file(file_id, path)

    def put_file(
        self, path: Path, path_api: str | Path | None, file_type: str
    ) -> requests.Response:
        # Get file upload pre-signed URL
        base_path = os.path.dirname(path_api) if path_api is not None else None
        response = session.post(
            self.file_post_url,
            params={"base_path": base_path, "type": file_type},
            headers=self._base_api.header,
        )

        # Upload file
        request_kwargs = response.json()
        file_name = (
            str(os.path.split(path_api)[-1]) if path_api is not None else path.name
        )
        f = {"file": (file_name, open(path, "rb"))}
        return session.request(**request_kwargs, files=f)

    def put_file_native(
        self, path: Path, f_type: FileType, path_api: Path
    ) -> requests.Response:
        return self.put_file(path, path_api, file_type=f_type)
