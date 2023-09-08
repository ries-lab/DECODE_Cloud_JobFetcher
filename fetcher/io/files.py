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

    def put(self, path: Path, filename: str | None = None):
        f = {"file": (path.stem if filename is None else filename, open(path, "rb"))}
        r = requests.post(self._url, files=f)
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
