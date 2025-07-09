import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

retry_strategy: Retry
adapter: HTTPAdapter
session: requests.Session
