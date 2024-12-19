import requests


def test_api_works(api_url: str) -> None:
    assert requests.get(f"{api_url}/").json() == {"message": "Hello World"}
