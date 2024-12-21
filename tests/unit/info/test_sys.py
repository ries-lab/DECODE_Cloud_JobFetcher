from unittest.mock import Mock, patch

from fetcher.info import sys


@patch("fetcher.info.sys.collect_host")
@patch("fetcher.info.sys.collect_os")
@patch("fetcher.info.sys.collect_sys")
@patch("fetcher.info.sys.collect_gpu")
def test_collect(
    mock_collect_gpu: Mock,
    mock_collect_sys: Mock,
    mock_collect_os: Mock,
    mock_collect_host: Mock,
) -> None:
    sys.collect()
    mock_collect_host.assert_called_once()
    mock_collect_os.assert_called_once()
    mock_collect_sys.assert_called_once()
    mock_collect_gpu.assert_called_once()


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
