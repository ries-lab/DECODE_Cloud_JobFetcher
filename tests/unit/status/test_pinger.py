import time
from typing import Type
from unittest.mock import Mock

import pytest

from decode_job_fetcher.status import pinger


@pytest.fixture
def mock_ping() -> Mock:
    return Mock(side_effect=(False, False, True))


@pytest.mark.parametrize(
    ("pinger_class", "t_exp"), [(pinger.ParallelPinger, 1), (pinger.SerialPinger, 2)]
)
def test_pinger(mock_ping: Mock, pinger_class: Type[pinger.Pinger], t_exp: int) -> None:
    pinger_ = pinger_class(mock_ping, timeout=0.5)
    t_start = time.time()
    pinger_.start()
    time.sleep(1)
    pinger_.stop()
    t_stop = time.time()
    t_diff = t_stop - t_start
    assert abs(t_diff - t_exp) <= 0.05
