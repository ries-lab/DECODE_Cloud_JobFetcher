"""
Test that the decode_job_fetcher package can be imported and used correctly.
"""
import pytest
import decode_job_fetcher


def test_package_import():
    """Test that the package can be imported correctly."""
    assert decode_job_fetcher.__version__ == "0.1.0"


def test_main_types_available():
    """Test that the main type definitions are available."""
    from decode_job_fetcher import FileType, Status
    
    # These should be Literal types
    assert hasattr(FileType, '__args__')
    assert hasattr(Status, '__args__')
    
    # Check that the literals contain expected values
    assert 'artifact' in FileType.__args__
    assert 'output' in FileType.__args__
    assert 'log' in FileType.__args__
    
    assert 'preprocessing' in Status.__args__
    assert 'running' in Status.__args__
    assert 'finished' in Status.__args__
    assert 'error' in Status.__args__


def test_main_api_classes_available():
    """Test that the main API classes are available."""
    from decode_job_fetcher import API, JobAPI, AccessToken, AccessTokenFixed, AccessTokenAuth
    
    # These should be classes
    assert callable(API)
    assert callable(JobAPI)
    assert callable(AccessTokenFixed)
    assert callable(AccessTokenAuth)
    
    # AccessToken should be an abstract base class
    assert hasattr(AccessToken, '__abstractmethods__')


def test_model_classes_available():
    """Test that the model classes are available."""
    from decode_job_fetcher import JobSpecs, HardwareSpecs, AppSpecs, HandlerSpecs, MetaSpecs
    
    # These should be Pydantic models
    assert hasattr(JobSpecs, '__annotations__')
    assert hasattr(HardwareSpecs, '__annotations__')
    assert hasattr(AppSpecs, '__annotations__')
    assert hasattr(HandlerSpecs, '__annotations__')
    assert hasattr(MetaSpecs, '__annotations__')


def test_submodules_available():
    """Test that the submodules are available."""
    from decode_job_fetcher import api, io, info, status, session
    
    # These should be modules
    assert hasattr(api, '__name__')
    assert hasattr(io, '__name__')
    assert hasattr(info, '__name__')
    assert hasattr(status, '__name__')
    assert hasattr(session, 'get')  # session should be a requests.Session


def test_all_exports():
    """Test that all expected exports are available."""
    from decode_job_fetcher import __all__
    
    # Check that all items in __all__ are actually available
    for item in __all__:
        assert hasattr(decode_job_fetcher, item), f"Item {item} not found in module"


def test_api_functionality():
    """Test that API classes can be instantiated."""
    from decode_job_fetcher import API, AccessTokenFixed
    
    # Should be able to create an API instance
    api = API("https://test.example.com")
    assert api.base_url == "https://test.example.com"
    
    # Should be able to create an AccessTokenFixed instance
    token = AccessTokenFixed("test_token")
    assert token.access_token == "test_token"


def test_model_functionality():
    """Test that model classes can be instantiated."""
    from decode_job_fetcher import HardwareSpecs, AppSpecs, HandlerSpecs, MetaSpecs, JobSpecs
    
    # Should be able to create model instances
    hardware = HardwareSpecs(cpu_cores=4, memory=8192)
    assert hardware.cpu_cores == 4
    assert hardware.memory == 8192
    
    app = AppSpecs(cmd=["python", "script.py"])
    assert app.cmd == ["python", "script.py"]
    
    handler = HandlerSpecs(image_url="https://example.com/image")
    assert handler.image_url == "https://example.com/image"
    
    meta = MetaSpecs(job_id=123, date_created="2023-01-01T00:00:00Z")
    assert meta.job_id == 123
    assert meta.date_created == "2023-01-01T00:00:00Z"
    
    # Should be able to create a complete JobSpecs
    job = JobSpecs(app=app, handler=handler, meta=meta, hardware=hardware)
    assert job.app == app
    assert job.handler == handler
    assert job.meta == meta
    assert job.hardware == hardware