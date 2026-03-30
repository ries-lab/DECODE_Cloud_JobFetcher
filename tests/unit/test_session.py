from fetcher.session import retry_strategy


def test_post_is_retried() -> None:
    assert retry_strategy.allowed_methods is not None
    assert "POST" in retry_strategy.allowed_methods


def test_all_methods_retried() -> None:
    expected = {"DELETE", "GET", "HEAD", "OPTIONS", "POST", "PUT", "TRACE"}
    assert retry_strategy.allowed_methods is not None
    assert expected == retry_strategy.allowed_methods


def test_retry_covers_server_errors() -> None:
    for code in [429, 500, 502, 503, 504]:
        assert code in retry_strategy.status_forcelist


def test_retry_budget_and_backoff() -> None:
    assert retry_strategy.total == 6
    assert retry_strategy.backoff_factor == 3
