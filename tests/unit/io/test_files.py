from pathlib import Path
from unittest import mock

import pytest

from fetcher.io import files


@pytest.mark.parametrize("delegate", ["rglob", "glob"])
def test_path_api_up_construction(delegate: str, tmp_path: Path) -> None:
    # tests that construction works from methods
    [
        (tmp_path / p).write_text("abc", encoding="utf8")
        for p in ["a.txt", "b.txt", "c.txt"]
    ]

    p = files.PathAPIUp(
        tmp_path,
        "output",
        Path(""),
        None,
    )
    p_files = list(getattr(p, delegate)("*"))

    for p in p_files:
        assert isinstance(p, files.PathAPIUp)


@pytest.mark.parametrize(
    ("path", "path_api", "expected"),
    [
        ("/a/b/c/d.txt", "/a/b/c", "d.txt"),
        ("/a/b/c/d.txt", "/a/b", "c/d.txt"),
    ],
)
def test_path_api_up_relative(path: str, path_api: str, expected: str) -> None:
    p = files.PathAPIUp(Path(path), "output", path_api, mock.MagicMock())
    assert str(p.path_api_rel) == expected


def test_path_api_up_push(tmp_path: Path) -> None:
    path = tmp_path / "test.txt"
    path.write_text("test")

    mock_api = mock.MagicMock()

    path_api_up = files.PathAPIUp(path, "output", tmp_path, mock_api)
    path_api_up.push()

    mock_api.put_file_native.assert_called_once_with(
        path_api_up._path, "output", Path("test.txt")
    )


def test_path_api_down_get(tmp_path: Path) -> None:
    mock_api = mock.MagicMock()
    p = files.PathAPIDown(tmp_path / "test.txt", "abcdefg", mock_api)
    p.get()

    assert not p.is_file()  # because of mock

    mock_api.get_file.assert_called_once_with("abcdefg", p._path)
