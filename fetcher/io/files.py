from abc import abstractmethod

import requests
from pathlib import Path


class Uploader:
    @abstractmethod
    def put(self, path: Path):
        raise NotImplementedError


class APIUploader(Uploader):
    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def put(self, path: Path, filename: str | None = None):
        f = {"file": (path.stem if filename is None else filename, open(path, "rb"))}
        requests.post(self._url, files=f)


class Downloader:
    def __init__(self, path: str | Path | None):
        self._path = (
            Path(path) if (path is not None and not isinstance(path, Path)) else path
        )

    @abstractmethod
    def get(self, url: str, path: Path):
        raise NotImplementedError
