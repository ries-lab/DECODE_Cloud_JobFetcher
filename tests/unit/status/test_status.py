from unittest.mock import Mock

import pytest

from fetcher.status import status


@pytest.fixture
def mock_ping() -> Mock:
    return Mock()


class TestConstantStatus:
    def test_ping(self, mock_ping: Mock) -> None:
        constant_status = status.ConstantStatus("running", mock_ping)
        constant_status.ping()
        mock_ping.assert_called_with("running", None, None)
        constant_status.update()
        constant_status.ping()
        mock_ping.assert_called_with("running", None, None)


class MockContainer:
    def __init__(self) -> None:
        self.attrs = {"State": {"Status": "running", "Running": True}}
        self.state_cycle = (
            s
            for s in [
                {"Status": "running", "Running": True},
                {"Status": "running", "Running": True},
                {"Status": "exited", "ExitCode": 0, "Running": False},
                {
                    "Status": "exited",
                    "ExitCode": 1,
                    "Error": "error",
                    "Running": False,
                },
            ]
        )

    def reload(self) -> None:
        self.attrs = {"State": next(self.state_cycle)}


class TestDockerStatus:
    @pytest.fixture
    def mock_container(self) -> MockContainer:
        return MockContainer()

    def test_ping_update_on_ping(
        self, mock_ping: Mock, mock_container: MockContainer
    ) -> None:
        docker_status = status.DockerStatus(
            mock_container,  # type: ignore
            mock_ping,
            update_on_ping=True,
        )
        assert docker_status.exited is False
        docker_status.ping()
        mock_ping.assert_called_with("running", None, None)
        assert docker_status.exited is False
        docker_status.ping()
        mock_ping.assert_called_with("running", None, None)
        assert docker_status.exited is False
        docker_status.ping()
        mock_ping.assert_called_with("postprocessing", 0, None)
        assert docker_status.exited is True
        docker_status.ping()
        mock_ping.assert_called_with("error", 1, "error")
        assert docker_status.exited is True

    def test_ping_no_update(
        self, mock_ping: Mock, mock_container: MockContainer
    ) -> None:
        docker_status = status.DockerStatus(
            mock_container,  # type: ignore
            mock_ping,
            update_on_ping=False,
        )
        docker_status.ping()
        mock_ping.assert_called_with("running", None, None)
        docker_status.ping()
        mock_ping.assert_called_with("running", None, None)
        docker_status.ping()
        mock_ping.assert_called_with("running", None, None)
        docker_status.update()
        docker_status.update()
        docker_status.update()
        docker_status.ping()
        mock_ping.assert_called_with("postprocessing", 0, None)
