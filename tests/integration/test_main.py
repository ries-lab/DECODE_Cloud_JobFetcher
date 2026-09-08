import os
from pathlib import Path

import docker
import pytest
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError

from cli import main
from scripts.docker import _get_client


@pytest.fixture
def path_host_base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture(autouse=True)
def mock_env(path_host_base: Path, api_url: str, mocker: MockerFixture):
    env_vars = {
        "API_URL": api_url,
        "USERNAME": "test_user",
        "PASSWORD": "test_password",
        "PATH_BASE": path_host_base.as_posix(),
        "PATH_HOST_BASE": path_host_base.as_posix(),
        "TIMEOUT_JOB": "1",
        "TIMEOUT_STATUS": "1",
    }
    mocker.patch.dict(main.os.environ, env_vars)
    mocker.patch.object(main.dotenv, "load_dotenv")
    return env_vars


@pytest.fixture(autouse=True)
def mock_cognito_auth(mocker: MockerFixture) -> None:
    mocker.patch.object(main.api.token, "AccessTokenAuth", return_value=None)


def test_successful_job_cleanup(path_host_base: Path, docker_image: str):
    main.main(max_iters=1)
    assert not os.listdir(path_host_base)
    assert not (
        [
            c
            for c in _get_client().containers.list(all=True)
            if docker_image in c.image.tags
        ]
    )


def test_failing_job_cleanup(
    path_host_base: Path, docker_image: str, mocker: MockerFixture
):
    original_auto_run = main.manager.Manager.auto_run

    def add_exit_code(*args, **kwargs) -> docker.models.containers.Container:
        env = kwargs.get("environment", {})
        env["EXIT_CODE"] = "1"
        kwargs["environment"] = env
        return original_auto_run(*args, **kwargs)

    mocker.patch.object(
        main.manager.Manager,
        "auto_run",
        add_exit_code,
    )
    main.main(max_iters=1)
    assert not os.listdir(path_host_base)
    assert not (
        [
            c
            for c in _get_client().containers.list(all=True)
            if docker_image in c.image.tags
        ]
    )


def test_no_job_available_no_cleanup(
    path_host_base: Path, mocker: MockerFixture
) -> None:
    """When no job is available no Docker container should be started and no
    filesystem resources should be created or removed."""
    mocker.patch.object(main.api.worker.API, "fetch_jobs", return_value={})

    main.main(max_iters=1)

    assert not os.listdir(path_host_base)


def test_container_remove_error_does_not_prevent_directory_cleanup(
    path_host_base: Path, docker_image: str, mocker: MockerFixture
) -> None:
    """A Docker error during container.remove() must be logged but must not prevent
    the job directory from being deleted."""
    original_auto_run = main.manager.Manager.auto_run
    saved_remove: dict = {}

    def capture_and_break_remove(
        *args: object, **kwargs: object
    ) -> docker.models.containers.Container:
        container = original_auto_run(*args, **kwargs)
        saved_remove["fn"] = container.remove
        mocker.patch.object(
            container, "remove", side_effect=Exception("Container remove failed")
        )
        return container

    mocker.patch.object(main.manager.Manager, "auto_run", capture_and_break_remove)

    main.main(max_iters=1)

    assert not os.listdir(path_host_base)

    # main() could not remove the container; clean it up so it does not linger.
    if "fn" in saved_remove:
        try:
            saved_remove["fn"]()
        except Exception:
            pass


def test_directory_cleanup_error_does_not_crash(
    path_host_base: Path, docker_image: str, mocker: MockerFixture
) -> None:
    """A failure to delete the job directory must be logged but must not crash
    the main loop."""
    rmtree_mock = mocker.patch.object(
        main.shutil, "rmtree", side_effect=OSError("Permission denied")
    )

    main.main(max_iters=1)

    rmtree_mock.assert_called_once()
    assert (path_host_base / "5").exists()  # directory survives the failed cleanup


def test_connection_error_on_fetch_does_not_crash(
    mock_env: dict, mocker: MockerFixture
) -> None:
    """A ConnectionError during job fetching should not crash the process."""
    fetch_mock = mocker.patch.object(main.api.worker.API, "fetch_jobs")
    fetch_mock.side_effect = [RequestsConnectionError("connection refused"), {}]
    sleep_mock = mocker.patch.object(main.time, "sleep")

    main.main(max_iters=2)  # must not raise

    sleep_mock.assert_called_with(
        1
    )  # TIMEOUT_JOB=1, called after error and after empty poll


def test_connection_error_mid_job_does_not_crash(
    tmp_path: Path, mock_env: dict, mocker: MockerFixture
) -> None:
    """A ConnectionError raised during job execution (status ping) should not crash
    the process, and all Docker/filesystem resources must still be cleaned up."""
    job_mock = mocker.MagicMock()
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

    mock_container = mocker.MagicMock()
    mock_container.status = "running"
    mock_manager = mocker.MagicMock()
    mock_manager.auto_run.return_value = mock_container
    mocker.patch("cli.main.manager.Manager", return_value=mock_manager)

    sleep_mock = mocker.patch.object(main.time, "sleep")

    main.main(max_iters=1)  # must not raise

    sleep_mock.assert_called_once_with(1)

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
    job_mock = mocker.MagicMock()
    job_mock.handler.files_up = None
    job_mock.handler.files_down = None

    mocker.patch.object(
        main.api.worker.API, "fetch_jobs", return_value={"job1": job_mock}
    )

    mocker.patch.object(main.status.pinger.ParallelPinger, "start")

    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mocker.patch.object(
        main.status.pinger.SerialPinger,
        "start",
        side_effect=HTTPError(response=mock_response),
    )

    mock_container = mocker.MagicMock()
    mock_container.status = "running"
    mock_manager = mocker.MagicMock()
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
    job_mock = mocker.MagicMock()
    job_mock.handler.files_up = {"log": "log"}
    job_mock.handler.files_down = None

    mocker.patch.object(
        main.api.worker.API, "fetch_jobs", return_value={"job1": job_mock}
    )

    mocker.patch.object(main.status.pinger.ParallelPinger, "start")
    mocker.patch.object(main.status.pinger.SerialPinger, "start")

    mock_container = mocker.MagicMock()
    mock_container.status = "exited"
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_manager = mocker.MagicMock()
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

    sleep_mock.assert_called_once_with(1)

    # Container already exited, so stop() must not be called — only remove()
    mock_container.reload.assert_called_once()
    mock_container.stop.assert_not_called()
    mock_container.remove.assert_called_once()

    # Job directory must be removed
    assert not (tmp_path / "job1").exists()
