import abc
import boto3
import datetime


class AccessToken(abc.ABC):
    @property
    @abc.abstractmethod
    def access_token(self) -> str:
        pass


class AccessTokenFixed(AccessToken):
    def __init__(self, access_token: str | None = None):
        self._access_token = access_token

    @property
    def access_token(self) -> str | None:
        return self._access_token


class AccessTokenAuth(AccessToken):
    def __init__(
        self, client_id: str, username: str, password: str, min_validity: int = 300
    ):
        """Token that is refreshed automatically when it is close to expiry."""
        self._client_id = client_id
        self._username = username
        self._password = password
        self._access_token = None
        self._expiry = None
        self._min_validity = min_validity
        self._cognito_client = boto3.client("cognito-idp")

    @property
    def access_token(self) -> str:
        if (
            self._access_token is None
            or self._expiry
            < datetime.datetime.utcnow()
            + datetime.timedelta(seconds=self._min_validity)
        ):
            self._refresh()
        return self._access_token

    def _refresh(self):
        response = self._cognito_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": self._username,
                "PASSWORD": self._password,
            },
            ClientId=self._client_id,
        )
        self._access_token = response["AuthenticationResult"]["IdToken"]
        self._expiry = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=response["AuthenticationResult"]["ExpiresIn"]
        )
