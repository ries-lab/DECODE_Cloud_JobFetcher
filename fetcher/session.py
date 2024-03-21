import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


# Retry for server errors at 5s, 10s, 20s, 40s, 80s, 160s
# (i.p., internal DB connection error might 500 for a couple of minutes)
retry_strategy = Retry(
    total=5,
    backoff_factor=3,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
# Always raise for status
session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
session.mount("http://", adapter)
session.mount("https://", adapter)
