import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Retry for server errors at 3s, 6s, 12s, 24s, 48s, 96s (~3 min total).
# POST is included so file uploads are also retried on transient failures.
retry_strategy = Retry(
    total=6,
    backoff_factor=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods={"DELETE", "GET", "HEAD", "OPTIONS", "POST", "PUT", "TRACE"},
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
# Always raise for status
session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
session.mount("http://", adapter)
session.mount("https://", adapter)
