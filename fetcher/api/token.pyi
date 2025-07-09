from typing import Any
import abc

class AccessToken(abc.ABC):
    @property
    @abc.abstractmethod
    def access_token(self) -> str: ...

class AccessTokenFixed(AccessToken):
    def __init__(self, access_token: str) -> None: ...
    @property
    def access_token(self) -> str: ...

class AccessTokenAuth(AccessToken):
    def __init__(
        self,
        client_id: str,
        region: str,
        username: str,
        password: str,
        min_validity: int = 300,
    ) -> None: ...
    @property
    def access_token(self) -> str: ...
    def _refresh(self) -> None: ...

def get_access_info(api_url: str) -> dict[str, Any]: ...
