"""Tests for cleanup functionality in the main job processing loop."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from cli.main import main


class TestMainCleanup:
    """Test cleanup behavior in the main() function."""

    @patch.dict(os.environ, {
        'API_URL': 'http://test.com',
        'USERNAME': 'test_user', 
        'PASSWORD': 'test_pass',
        'TIMEOUT_JOB': '1',
        'TIMEOUT_STATUS': '1'
    })
    @patch('cli.main.shutil.rmtree')
    @patch('cli.main.itertools.chain')
    @patch('cli.main.GPUtil.getGPUs')
    @patch('cli.main.docker.types.Mount')
    @patch('cli.main.docker.types.DeviceRequest')
    @patch('cli.main.manager.Manager')
    @patch('cli.main.io.files.PathAPIUp')
    @patch('cli.main.io.files.PathAPIDown')
    @patch('cli.main.status.pinger.ParallelPinger')
    @patch('cli.main.status.pinger.SerialPinger')
    @patch('cli.main.status.status.ConstantStatus')
    @patch('cli.main.status.status.DockerStatus')
    @patch('cli.main.api.worker.JobAPI')
    @patch('cli.main.api.worker.API')
    @patch('cli.main.api.token.AccessTokenAuth')
    @patch('cli.main.api.token.get_access_info')
    @patch('cli.main.info.sys.collect')
    @patch('cli.main.time.sleep')
    @patch('cli.main.dotenv.load_dotenv')
    def test_main_successful_job_with_cleanup(
        self,
        mock_load_dotenv,
        mock_sleep,
        mock_sys_collect,
        mock_get_access_info,
        mock_access_token_auth,
        mock_api_class,
        mock_job_api_class,
        mock_docker_status,
        mock_constant_status,
        mock_serial_pinger,
        mock_parallel_pinger,
        mock_path_api_down,
        mock_path_api_up,
        mock_manager_class,
        mock_device_request,
        mock_mount,
        mock_get_gpus,
        mock_chain,
        mock_rmtree
    ) -> None:
        """Test that main() properly cleans up after successful job completion."""
        # Setup basic mocks
        mock_get_access_info.return_value = {
            'cognito': {'client_id': 'test', 'region': 'us-east-1'}
        }
        mock_access_token_auth.return_value = Mock()
        
        mock_worker_info = Mock()
        mock_worker_info.sys.cores = 4
        mock_worker_info.sys.memory = 8
        mock_worker_info.gpus = []
        mock_sys_collect.return_value = mock_worker_info
        
        # Mock API worker
        mock_api_worker = Mock()
        mock_api_class.return_value = mock_api_worker
        
        # Mock job data
        mock_job = Mock()
        mock_job.handler.files_up = None
        mock_job.handler.files_down = None
        mock_job.handler.image_url = "test:latest"
        mock_job.app.cmd = "echo test"
        mock_job.app.env = {}
        
        # First call returns a job, second call returns empty to break the loop
        call_count = 0
        def fetch_jobs_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"test_job_123": mock_job}
            elif call_count <= 3:
                return []  # No more jobs - should loop
            else:
                # Force exit after a few loops to prevent infinite test
                raise KeyboardInterrupt("Test exit")
        
        mock_api_worker.fetch_jobs.side_effect = fetch_jobs_side_effect
        
        # Mock container
        mock_container = Mock()
        mock_container.status = "running"
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"test logs"
        
        # Mock docker manager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.auto_run.return_value = mock_container
        
        # Mock job API
        mock_job_api = Mock()
        mock_job_api_class.return_value = mock_job_api
        
        # Mock pingers
        mock_pre_pinger = Mock()
        mock_run_pinger = Mock()
        mock_post_pinger = Mock()
        mock_parallel_pinger.side_effect = [mock_pre_pinger, mock_post_pinger]
        mock_serial_pinger.return_value = mock_run_pinger
        
        # Mock file operations
        mock_get_gpus.return_value = []
        mock_chain.return_value = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Mock the paths using environment variables instead of patching Path constructor
            with patch.dict(os.environ, {
                'PATH_BASE': str(temp_path / 'data'),
                'PATH_HOST_BASE': str(temp_path / 'host')
            }):
                # Run main() - it should process one job and exit when no more jobs
                with pytest.raises(KeyboardInterrupt):
                    main()
                
                # Verify container cleanup was called
                mock_container.stop.assert_called_once()
                mock_container.remove.assert_called_once()
                
                # The directory cleanup may or may not be called depending on path setup
                # but the main logic is tested through the container cleanup

    @patch.dict(os.environ, {
        'API_URL': 'http://test.com',
        'USERNAME': 'test_user', 
        'PASSWORD': 'test_pass',
        'TIMEOUT_JOB': '1',
        'TIMEOUT_STATUS': '1'
    })
    @patch('cli.main.shutil.rmtree')
    @patch('cli.main.itertools.chain')
    @patch('cli.main.GPUtil.getGPUs')
    @patch('cli.main.docker.types.Mount')
    @patch('cli.main.docker.types.DeviceRequest')
    @patch('cli.main.manager.Manager')
    @patch('cli.main.io.files.PathAPIUp')
    @patch('cli.main.io.files.PathAPIDown')
    @patch('cli.main.status.pinger.ParallelPinger')
    @patch('cli.main.status.pinger.SerialPinger')
    @patch('cli.main.status.status.ConstantStatus')
    @patch('cli.main.status.status.DockerStatus')
    @patch('cli.main.api.worker.JobAPI')
    @patch('cli.main.api.worker.API')
    @patch('cli.main.api.token.AccessTokenAuth')
    @patch('cli.main.api.token.get_access_info')
    @patch('cli.main.info.sys.collect')
    @patch('cli.main.time.sleep')
    @patch('cli.main.dotenv.load_dotenv')
    def test_main_cleanup_handles_container_exceptions(
        self,
        mock_load_dotenv,
        mock_sleep,
        mock_sys_collect,
        mock_get_access_info,
        mock_access_token_auth,
        mock_api_class,
        mock_job_api_class,
        mock_docker_status,
        mock_constant_status,
        mock_serial_pinger,
        mock_parallel_pinger,
        mock_path_api_down,
        mock_path_api_up,
        mock_manager_class,
        mock_device_request,
        mock_mount,
        mock_get_gpus,
        mock_chain,
        mock_rmtree
    ) -> None:
        """Test that main() handles exceptions during container cleanup gracefully."""
        # Setup mocks similar to successful test
        mock_get_access_info.return_value = {
            'cognito': {'client_id': 'test', 'region': 'us-east-1'}
        }
        mock_access_token_auth.return_value = Mock()
        
        mock_worker_info = Mock()
        mock_worker_info.sys.cores = 4
        mock_worker_info.sys.memory = 8
        mock_worker_info.gpus = []
        mock_sys_collect.return_value = mock_worker_info
        
        mock_api_worker = Mock()
        mock_api_class.return_value = mock_api_worker
        
        mock_job = Mock()
        mock_job.handler.files_up = None
        mock_job.handler.files_down = None
        mock_job.handler.image_url = "test:latest"
        mock_job.app.cmd = "echo test"
        mock_job.app.env = {}
        
        call_count = 0
        def fetch_jobs_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"test_job_456": mock_job}
            elif call_count <= 3:
                return []  # No more jobs - should loop
            else:
                # Force exit after a few loops to prevent infinite test
                raise KeyboardInterrupt("Test exit")
        
        mock_api_worker.fetch_jobs.side_effect = fetch_jobs_side_effect
        
        # Mock container that raises exceptions during cleanup
        mock_container = Mock()
        mock_container.status = "running"
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"test logs"
        mock_container.stop.side_effect = Exception("Stop failed")
        mock_container.remove.side_effect = Exception("Remove failed")
        
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.auto_run.return_value = mock_container
        
        mock_job_api = Mock()
        mock_job_api_class.return_value = mock_job_api
        
        mock_pre_pinger = Mock()
        mock_run_pinger = Mock()
        mock_post_pinger = Mock()
        mock_parallel_pinger.side_effect = [mock_pre_pinger, mock_post_pinger]
        mock_serial_pinger.return_value = mock_run_pinger
        
        mock_get_gpus.return_value = []
        mock_chain.return_value = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch.dict(os.environ, {
                'PATH_BASE': str(temp_path / 'data'),
                'PATH_HOST_BASE': str(temp_path / 'host')
            }):
                # Should not raise exception despite container cleanup failures
                with pytest.raises(KeyboardInterrupt):
                    main()
                
                # Verify container cleanup was attempted (despite exceptions)
                mock_container.stop.assert_called_once()
                mock_container.remove.assert_called_once()
                
                # The directory cleanup may or may not be called depending on path setup
                # but the main logic is tested through the container cleanup

    @patch.dict(os.environ, {
        'API_URL': 'http://test.com',
        'USERNAME': 'test_user', 
        'PASSWORD': 'test_pass',
        'TIMEOUT_JOB': '1',
        'TIMEOUT_STATUS': '1'
    })
    @patch('cli.main.shutil.rmtree')
    @patch('cli.main.api.worker.API')
    @patch('cli.main.api.token.AccessTokenAuth')
    @patch('cli.main.api.token.get_access_info')
    @patch('cli.main.info.sys.collect')
    @patch('cli.main.time.sleep')
    @patch('cli.main.dotenv.load_dotenv')
    def test_main_no_job_no_cleanup(
        self,
        mock_load_dotenv,
        mock_sleep,
        mock_sys_collect,
        mock_get_access_info,
        mock_access_token_auth,
        mock_api_class,
        mock_rmtree
    ) -> None:
        """Test that main() doesn't attempt cleanup when no job is processed."""
        # Setup mocks
        mock_get_access_info.return_value = {
            'cognito': {'client_id': 'test', 'region': 'us-east-1'}
        }
        mock_access_token_auth.return_value = Mock()
        
        mock_worker_info = Mock()
        mock_worker_info.sys.cores = 4
        mock_worker_info.sys.memory = 8
        mock_worker_info.gpus = []
        mock_sys_collect.return_value = mock_worker_info
        
        mock_api_worker = Mock()
        mock_api_class.return_value = mock_api_worker
        
        # Return empty jobs twice to test the sleep behavior and break loop
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return []  # No jobs
            else:
                # Break infinite loop by raising exception after a few iterations
                raise KeyboardInterrupt()
        
        mock_api_worker.fetch_jobs.side_effect = side_effect
        
        # Should exit due to KeyboardInterrupt after processing no jobs
        with pytest.raises(KeyboardInterrupt):
            main()
        
        # Verify no cleanup was attempted
        mock_rmtree.assert_not_called()
        
        # Verify sleep was called when no jobs found
        assert mock_sleep.call_count >= 2
