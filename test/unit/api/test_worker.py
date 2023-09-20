from fetcher.api import worker


def test_api():
    api = worker.API("http://localhost:8000")
    assert api.build_file_url("abc") == "http://localhost:8000/file_url/abc"


def test_job_api():
    api = worker.JobAPI("abc", worker.API("http://localhost:8000"))
    assert api.job_url == "http://localhost:8000/jobs/abc"
    assert api.status_url == "http://localhost:8000/jobs/abc/status"
    assert api.file_post_url == "http://localhost:8000/jobs/abc/file"
