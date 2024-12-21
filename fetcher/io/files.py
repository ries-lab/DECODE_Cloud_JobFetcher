from abc import abstractmethod
from pathlib import Path
from typing import Any, Generator, Literal

import requests

from fetcher.api import worker
from fetcher.session import session


class PathAPIbase:
    _path: Path

    def __str__(self) -> str:
        return str(self._path)

    def __getattr__(self, attr: str) -> Any:
        # Delegate to the underlying _path object
        return getattr(self._path, attr)


class PathAPIUp(PathAPIbase):
    def __init__(
        self,
        path: str | Path,
        f_type: Literal["artifact", "output", "log"],
        path_api: str | Path,
        api: worker.JobAPI,
    ):
        """

        Args:
            path:
            path_api: path to make path relative to in API world
            api: api backend
        """
        self._path = Path(path) if not isinstance(path, Path) else path
        self._f_type = f_type
        self._path_api = Path(path_api) if not isinstance(path_api, Path) else path_api
        self._api = api

    @property
    def path_api_rel(self) -> Path:
        """
        API-relative path
        """
        return self._path.relative_to(self._path_api)

    def __repr__(self) -> str:
        return f"PathAPIUp({repr(self._path)}, {repr(self._f_type)}, {repr(self._path_api)}, {repr(self._api)})"

    def push(self) -> requests.Response:
        if self._path.is_dir():
            raise NotImplementedError("Directory upload not implemented")
        return self._api.put_file_native(self._path, self._f_type, self.path_api_rel)

    def glob(self, pattern: str) -> Generator["PathAPIUp", Any, None]:
        return (
            type(self)(p, self._f_type, self._path_api, self._api)
            for p in self._path.glob(pattern)
        )

    def rglob(self, pattern: str) -> Generator["PathAPIUp", Any, None]:
        return (
            type(self)(p, self._f_type, self._path_api, self._api)
            for p in self._path.rglob(pattern)
        )


class PathAPIDown(PathAPIbase):
    def __init__(self, path: str | Path, file_id: str, api: worker.JobAPI):
        self._path = Path(path) if not isinstance(path, Path) else path
        self._file_id = file_id
        self._api = api

    def __repr__(self) -> str:
        return (
            f"PathAPIDown({repr(self._path)}, {repr(self._file_id)}, {repr(self._api)})"
        )

    def get(self, mkdir: bool = True, parents: bool = True) -> requests.Response:
        if mkdir:
            self._path.parent.mkdir(parents=parents, exist_ok=True)
        return self._api.get_file(self._file_id, self._path)


class Uploader:
    @abstractmethod
    def put(
        self, path: Path, type: str, path_api: str | None = None
    ) -> requests.Response:
        raise NotImplementedError


class APIUploader(Uploader):
    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def put(
        self, path: Path, type: str, path_api: str | None = None
    ) -> requests.Response:
        path_api = path.stem if path_api is None else path_api
        f = {"file": (path_api, open(path, "rb"))}
        response = session.post(
            self._url, params={"path": path_api, "type": type}, files=f
        )
        return response


class Downloader:
    def __init__(self, path: str | Path | None):
        self._path = (
            Path(path) if (path is not None and not isinstance(path, Path)) else path
        )

    @abstractmethod
    def get(self, url: str, path: Path) -> requests.Response:
        raise NotImplementedError


class APIDownloader(Downloader):
    def get(self, url: str, path: Path) -> requests.Response:
        response = session.get(url, allow_redirects=True)
        path = path if path is not None else self._path
        with path.open("wb") as f:
            f.write(response.content)
        return response
