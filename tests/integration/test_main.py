import os
from pathlib import Path

import docker
import pytest
from pytest_mock import MockerFixture

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
