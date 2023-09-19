from abc import abstractmethod
from pathlib import Path

import requests

from fetcher.api import worker


class PathAPIUp:
    def __init__(
        self,
        path: str | Path,
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
        self._path_api = Path(path_api) if not isinstance(path_api, Path) else path_api
        self._api = api

    @property
    def path_api_rel(self):
        """
        API-relative path
        """
        return self._path.relative_to(self._path_api)

    def __str__(self):
        return str(self._path)

    def __repr__(self):
        return (
            f"PathAPIUp({repr(self._path)}, {repr(self._api)})"
            f"PathAPIUp({repr(self._path)}, {repr(self._api)})"
        )

    def __getattr__(self, attr):
        # Delegate to the underlying _path object
        return getattr(self._path, attr)

    def push(self):
        self._api.put_file_native(self._path, self.path_api_rel)

    def glob(self, pattern: str):
        return (
            type(self)(p, self._path_api, self._api) for p in self._path.glob(pattern)
        )

    def rglob(self, pattern: str):
        return (
            type(self)(p, self._path_api, self._api) for p in self._path.rglob(pattern)
        )


class PathAPItracked(Path):
    def __init__(
        self,
        path: str | Path,
        file_id: str | None,
        path_api: str | None,
        api,
        api_upload_type: str | None,
    ):
        """

        Args:
            path: local path
            file_id: file ID on API for downloading
            path_api: relative path on API for uploading
            api: api binder
            api_upload_type: type of upload, e.g. "artifact"
        """
        super().__init__(path)

        self._path_api = path_api
        self._api = api
        self._api_upload_type = api_upload_type

    def get(self):
        pass


class Uploader:
    @abstractmethod
    def put(self, path: Path):
        raise NotImplementedError


class APIUploader(Uploader):
    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def put(self, path: Path, type: str, path_api: str | None = None):
        path_api = path.stem if path_api is None else path_api
        f = {"file": (path_api, open(path, "rb"))}
        r = requests.post(self._url, params={"path": path_api, "type": type}, files=f)
        r.raise_for_status()


class Downloader:
    def __init__(self, path: str | Path | None):
        self._path = (
            Path(path) if (path is not None and not isinstance(path, Path)) else path
        )

    @abstractmethod
    def get(self, url: str, path: Path):
        raise NotImplementedError


class APIDownloader(Downloader):
    def get(self, url: str, path: Path):
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()

        path = path if path is not None else self._path
        with path.open("wb") as f:
            f.write(r.content)
