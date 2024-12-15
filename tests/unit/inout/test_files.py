from pathlib import Path
from unittest import mock

import pytest

from fetcher.io import files


@pytest.mark.parametrize("delegate", ["rglob", "glob"])
def test_path_api_up_construction(delegate, tmpdir):
    # tests that construction works from methods
    [
        (tmpdir / p).write_text("abc", encoding="utf8")
        for p in ["a.txt", "b.txt", "c.txt"]
    ]

    p = files.PathAPIUp(Path(tmpdir), "output", Path(""), None)
    p_files = list(getattr(p, delegate)("*"))

    for p in p_files:
        assert isinstance(p, files.PathAPIUp)


@pytest.mark.parametrize(
    "path,path_api,expected",
    [
        ("/a/b/c/d.txt", "/a/b/c", "d.txt"),
        ("/a/b/c/d.txt", "/a/b", "c/d.txt"),
    ],
)
def test_path_api_up_relative(path, path_api, expected):
    path = Path(path)

    p = files.PathAPIUp(path, "output", path_api, mock.MagicMock())
    assert str(p.path_api_rel) == expected


def test_path_api_up_push(tmpdir):
    p = Path(tmpdir) / "test.txt"
    p.write_text("test")

    mock_api = mock.MagicMock()

    p = files.PathAPIUp(p, "output", tmpdir, mock_api)
    p.push()

    mock_api.put_file_native.assert_called_once_with(
        p._path, "output", Path("test.txt")
    )


def test_path_api_down_get(tmpdir):
    p = Path(tmpdir) / "test.txt"

    mock_api = mock.MagicMock()
    p = files.PathAPIDown(p, "abcdefg", mock_api)
    p.get()

    assert not p.is_file()  # because of mock

    mock_api.get_file.assert_called_once_with("abcdefg", p._path)


@pytest.mark.parametrize("filename", [None, "test.txt"])
def test_api_uploader(tmpdir, filename):
    url = "http://localhost:8000/file"
    up = files.APIUploader(url)

    p = Path(tmpdir) / "test.txt"
    p.write_text("test")

    with mock.patch("requests.post") as mock_post:
        up.put(p, filename)

    mock_post.assert_called_once()


def test_downloader(tmpdir):
    url = "http://localhost:8000/file"
    down = files.APIDownloader(None)

    p = Path(tmpdir) / "test.txt"
    with mock.patch("requests.get") as mock_get:
        m_return = mock.MagicMock()
        m_return.content = b"test"
        mock_get.return_value = m_return

        down.get(url, p)

    mock_get.assert_called_once()
