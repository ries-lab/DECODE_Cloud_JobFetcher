

class API:
    def __init__(self, url: str):
        self.url = url

    def __truediv__(self, other):
        return API(f"{self.url}/{other}")


class JobAPI(API):
    def __init__(self, job_id: str, api: API):
        super().__init__(f"{api.url}/{job_id}")
        self.job_id = job_id

    @property
    def file(self):
        return self / "file"

    @property
    def status(self):
        return self / "status"
