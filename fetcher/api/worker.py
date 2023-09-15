import requests


class API:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_job(self, params: Dict[str, Any]) -> 'Job':
        response = self._request("GET", "/job", params=params)
        return Job(self, response)

    def build_file_url(self, file_id: str) -> str:
        return f"{self.base_url}/file_url/{file_id}"

    def build_job_file_url(self, job_id: str) -> str:
        return f"{self.base_url}/job/{job_id}/file"

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = self.base_url + endpoint
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
