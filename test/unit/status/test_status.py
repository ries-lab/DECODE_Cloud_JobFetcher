import pytest
from unittest import mock

from fetcher import status


def test_keepalive():
    p = mock.create_autospec(status.ping.Ping)
