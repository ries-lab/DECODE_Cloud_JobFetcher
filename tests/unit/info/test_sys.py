from unittest import mock

from fetcher.info import sys


@mock.patch("fetcher.info.sys.collect_host")
@mock.patch("fetcher.info.sys.collect_os")
@mock.patch("fetcher.info.sys.collect_sys")
@mock.patch("fetcher.info.sys.collect_gpu")
def test_collect(mock_collect_gpu, mock_collect_sys, mock_collect_os, mock_collect_host):
    sys.collect()
    mock_collect_host.assert_called_once()
    mock_collect_os.assert_called_once()
    mock_collect_sys.assert_called_once()
    mock_collect_gpu.assert_called_once()


def test_host():
    assert "hostname" in sys.collect_host()


def test_os():
    out = sys.collect_os()
    assert "system" in out
    assert "release" in out
    assert "version" in out
    assert "alias" in out


def test_sys():
    out = sys.collect_sys()
    assert "architecture" in out
    assert "cores" in out
    assert "memory" in out


def test_gpu():
    out = sys.collect_gpu()
    assert isinstance(out, list)
