from pathlib import Path
from unittest import mock

import pytest

from fetcher.io import files


@pytest.mark.parametrize("filename", [None, "test.txt"])
def test_api_uploader(api_url: str, tmp_path: Path, filename: str) -> None:
    url = f"{api_url}/file"
    up = files.APIUploader(url)

    p = tmp_path / "test.txt"
    p.write_text("test")

    with mock.patch("fetcher.io.files.session.post") as mock_post:
        up.put(p, filename)

    mock_post.assert_called_once()


def test_api_downloader(api_url: str, tmp_path: Path) -> None:
    url = f"{api_url}/file"
    down = files.APIDownloader(None)

    p = tmp_path / "test.txt"
    with mock.patch("fetcher.io.files.session.get") as mock_get:
        m_return = mock.MagicMock(content=b"test")
        mock_get.return_value = m_return

        down.get(url, p)

    mock_get.assert_called_once()
