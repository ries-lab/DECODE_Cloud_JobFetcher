import abc
import datetime
from typing import Any

import boto3

from ..session import session


def get_access_info(api_url: str) -> dict[str, Any]:
    response = session.get(f"{api_url}/access_info")
    return response.json()  # type: ignore


class AccessToken(abc.ABC):
    @property
    @abc.abstractmethod
    def access_token(self) -> str:
        pass


class AccessTokenFixed(AccessToken):
    def __init__(self, access_token: str):
        self._access_token = access_token

    @property
    def access_token(self) -> str:
        return self._access_token


class AccessTokenAuth(AccessToken):
    def __init__(
        self,
        client_id: str,
        region: str,
        username: str,
        password: str,
        min_validity: int = 300,
    ):
        """Token that is refreshed automatically when it is close to expiry."""
        self._client_id = client_id
        self._username = username
        self._password = password
        self._min_validity = min_validity
        self._cognito_client = boto3.client("cognito-idp", region_name=region)
        self._refresh()

    @property
    def access_token(self) -> str:
        if self._expiry < datetime.datetime.now(
            tz=datetime.timezone.utc
        ) + datetime.timedelta(seconds=self._min_validity):
            self._refresh()
        return self._access_token

    def _refresh(self) -> None:
        response = self._cognito_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": self._username,
                "PASSWORD": self._password,
            },
            ClientId=self._client_id,
        )
        self._access_token: str = response["AuthenticationResult"]["IdToken"]
        self._expiry = datetime.datetime.now(
            tz=datetime.timezone.utc
        ) + datetime.timedelta(seconds=response["AuthenticationResult"]["ExpiresIn"])
