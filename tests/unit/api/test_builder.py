from decode_job_fetcher.api import builder


def test_api() -> None:
    api = builder.API("http://localhost:8000")
    assert (api / "a" / "b").url == "http://localhost:8000/a/b"


def test_job_api() -> None:
    api = builder.API("http://localhost:8000/job")
    job_api = builder.JobAPI("a6", api)

    assert (job_api / "file").url == "http://localhost:8000/job/a6/file"
    assert (job_api / "status").url == "http://localhost:8000/job/a6/status"
