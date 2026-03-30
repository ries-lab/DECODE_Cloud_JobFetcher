from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError

from cli import main


@pytest.fixture
def mock_env(tmp_path: Path, mocker: MockerFixture) -> dict:
    env_vars = {
        "API_URL": "http://localhost:9999",
        "USERNAME": "u",
        "PASSWORD": "p",
        "PATH_BASE": tmp_path.as_posix(),
        "PATH_HOST_BASE": tmp_path.as_posix(),
        "TIMEOUT_JOB": "0",
        "TIMEOUT_STATUS": "0",
    }
    mocker.patch.dict(main.os.environ, env_vars)
    mocker.patch.object(main.dotenv, "load_dotenv")
    mocker.patch.object(
        main.api.token,
        "get_access_info",
        return_value={"cognito": {"client_id": "x", "region": "r"}},
    )
    mocker.patch.object(main.api.token, "AccessTokenAuth", return_value=None)
    worker_info = MagicMock()
    worker_info.gpus = []
    mocker.patch.object(main.info.sys, "collect", return_value=worker_info)
    return env_vars


def test_connection_error_on_fetch_does_not_crash(
    mock_env: dict, mocker: MockerFixture
) -> None:
    """A ConnectionError during job fetching should not crash the process."""
    fetch_mock = mocker.patch.object(main.api.worker.API, "fetch_jobs")
    fetch_mock.side_effect = [RequestsConnectionError("connection refused"), {}]
    sleep_mock = mocker.patch.object(main.time, "sleep")

    main.main(max_iters=2)  # must not raise

    sleep_mock.assert_called_with(
        0
    )  # TIMEOUT_JOB=0, called after error and after empty poll


def test_connection_error_mid_job_does_not_crash(
    tmp_path: Path, mock_env: dict, mocker: MockerFixture
) -> None:
    """A ConnectionError raised during job execution (status ping) should not crash
    the process, and all Docker/filesystem resources must still be cleaned up."""
    job_mock = MagicMock()
    job_mock.handler.files_up = None
    job_mock.handler.files_down = None

    mocker.patch.object(
        main.api.worker.API, "fetch_jobs", return_value={"job1": job_mock}
    )

    # Suppress the preprocessing pinger (runs in a thread – we don't need it here)
    mocker.patch.object(main.status.pinger.ParallelPinger, "start")

    # Make the running-phase SerialPinger raise to simulate API going down mid-job
    mocker.patch.object(
        main.status.pinger.SerialPinger,
        "start",
        side_effect=RequestsConnectionError("API down"),
    )

    mock_container = MagicMock()
    mock_container.status = "running"
    mock_manager = MagicMock()
    mock_manager.auto_run.return_value = mock_container
    mocker.patch("cli.main.manager.Manager", return_value=mock_manager)

    sleep_mock = mocker.patch.object(main.time, "sleep")

    main.main(max_iters=1)  # must not raise

    sleep_mock.assert_called_once_with(0)

    # Container must be stopped and removed despite the error
    mock_container.reload.assert_called_once()
    mock_container.stop.assert_called_once()
    mock_container.remove.assert_called_once()

    # Job directory must be removed
    assert not (tmp_path / "job1").exists()


def test_http_404_kills_container_and_cleans_up(
    tmp_path: Path, mock_env: dict, mocker: MockerFixture
) -> None:
    """An HTTP 404 (job deleted by user mid-run) should kill the running container
    and still clean up all resources; the loop must not crash."""
    job_mock = MagicMock()
    job_mock.handler.files_up = None
    job_mock.handler.files_down = None

    mocker.patch.object(
        main.api.worker.API, "fetch_jobs", return_value={"job1": job_mock}
    )

    mocker.patch.object(main.status.pinger.ParallelPinger, "start")

    mock_response = MagicMock()
    mock_response.status_code = 404
    mocker.patch.object(
        main.status.pinger.SerialPinger,
        "start",
        side_effect=HTTPError(response=mock_response),
    )

    mock_container = MagicMock()
    mock_container.status = "running"
    mock_manager = MagicMock()
    mock_manager.auto_run.return_value = mock_container
    mocker.patch("cli.main.manager.Manager", return_value=mock_manager)

    sleep_mock = mocker.patch.object(main.time, "sleep")

    main.main(max_iters=1)  # must not raise

    # Container must be killed (404 handler) then stopped and removed (finally)
    mock_container.kill.assert_called_once()
    mock_container.reload.assert_called_once()
    mock_container.stop.assert_called_once()
    mock_container.remove.assert_called_once()

    # Job directory must be removed
    assert not (tmp_path / "job1").exists()

    # No sleep: 404 is not a transient error that warrants a back-off
    sleep_mock.assert_not_called()


def test_upload_failure_cleans_up(
    tmp_path: Path, mock_env: dict, mocker: MockerFixture
) -> None:
    """A ConnectionError during file upload should trigger cleanup of the container
    and job directory; the loop must not crash."""
    job_mock = MagicMock()
    job_mock.handler.files_up = {"log": "log"}
    job_mock.handler.files_down = None

    mocker.patch.object(
        main.api.worker.API, "fetch_jobs", return_value={"job1": job_mock}
    )

    mocker.patch.object(main.status.pinger.ParallelPinger, "start")
    mocker.patch.object(main.status.pinger.SerialPinger, "start")

    mock_container = MagicMock()
    mock_container.status = "exited"
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_manager = MagicMock()
    mock_manager.auto_run.return_value = mock_container
    mocker.patch("cli.main.manager.Manager", return_value=mock_manager)

    # Put a file into the upload directory so push() is actually invoked
    log_dir = tmp_path / "job1" / "log"
    log_dir.mkdir(parents=True)
    (log_dir / "output.log").write_text("logs")

    mocker.patch.object(
        main.io.files.PathAPIUp,
        "push",
        side_effect=RequestsConnectionError("upload failed"),
    )

    sleep_mock = mocker.patch.object(main.time, "sleep")

    main.main(max_iters=1)  # must not raise

    sleep_mock.assert_called_once_with(0)

    # Container already exited, so stop() must not be called — only remove()
    mock_container.reload.assert_called_once()
    mock_container.stop.assert_not_called()
    mock_container.remove.assert_called_once()

    # Job directory must be removed
    assert not (tmp_path / "job1").exists()
