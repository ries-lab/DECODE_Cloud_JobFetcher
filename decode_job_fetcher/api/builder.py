class API:
    def __init__(self, url: str):
        self.url = url

    def __truediv__(self, other: str) -> "API":
        return API(f"{self.url}/{other}")


class JobAPI(API):
    def __init__(self, job_id: str, api: API):
        super().__init__(f"{api.url}/{job_id}")
        self.job_id = job_id

    @property
    def file(self) -> "API":
        return self / "files" / "url"

    @property
    def status(self) -> "API":
        return self / "status"
