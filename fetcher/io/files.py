from abc import abstractmethod
from pathlib import Path

import requests


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
