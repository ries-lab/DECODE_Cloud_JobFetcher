from pytest_mock import MockerFixture

from decode_job_fetcher.info import sys


def test_collect(mocker: MockerFixture) -> None:
    mock_collect_host = mocker.spy(sys, "collect_host")
    mock_collect_os = mocker.spy(sys, "collect_os")
    mock_collect_sys = mocker.spy(sys, "collect_sys")
    mock_collect_gpus = mocker.spy(sys, "collect_gpus")
    sys.collect()
    mock_collect_host.assert_called_once()
    mock_collect_os.assert_called_once()
    mock_collect_sys.assert_called_once()
    mock_collect_gpus.assert_called_once()


def test_host() -> None:
    assert "hostname" in sys.collect_host().model_dump()


def test_os() -> None:
    out = sys.collect_os()
    assert "system" in out.model_dump()
    assert "release" in out.model_dump()
    assert "version" in out.model_dump()
    assert "alias" in out.model_dump()


def test_sys() -> None:
    out = sys.collect_sys()
    assert "architecture" in out.model_dump()
    assert "cores" in out.model_dump()
    assert "memory" in out.model_dump()


def test_gpu() -> None:
    out = sys.collect_gpus()
    assert isinstance(out, list)
