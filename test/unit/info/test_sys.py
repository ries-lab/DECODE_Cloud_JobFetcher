from fetcher.info import sys


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
