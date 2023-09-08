from pathlib import Path
from unittest import mock

import pytest

from fetcher.io import files


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
    with (mock.patch("requests.get") as mock_get):
        m_return = mock.MagicMock()
        m_return.content = b"test"
        mock_get.return_value = m_return

        down.get(url, p)

    mock_get.assert_called_once()

