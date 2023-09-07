from abc import abstractmethod
from typing import Literal
import requests


class Ping:
    @abstractmethod
    def ping(
        self,
        status: Literal["running", "stopped", "error"],
        exit_code: int | None,
        body: str,
    ):
        raise NotImplementedError


class APIPing(Ping):
    def __init__(self, url: str):
        self._url = url

    def ping(
        self,
        status: Literal["running", "stopped", "error"],
        exit_code: int | None,
        body: str,
    ):
        requests.put(
            self._url,
            params={"status": status},
            json={"exit_code": exit_code, "status_body": body},
        )
