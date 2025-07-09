"""DECODE Job Fetcher Library

This library provides functionality for fetching and managing jobs from DECODE Cloud.
"""

# Main API components
from . import api as api
from . import io as io
from . import info as info
from . import status as status

# Core models and types
from .models import FileType as FileType
from .models import Status as Status

# Session management
from .session import session as session

# Main API classes
from .api.worker import API as API
from .api.worker import JobAPI as JobAPI
from .api.token import AccessToken as AccessToken
from .api.token import AccessTokenFixed as AccessTokenFixed
from .api.token import AccessTokenAuth as AccessTokenAuth

# Model classes
from .api.model import JobSpecs as JobSpecs
from .api.model import HardwareSpecs as HardwareSpecs
from .api.model import AppSpecs as AppSpecs
from .api.model import HandlerSpecs as HandlerSpecs
from .api.model import MetaSpecs as MetaSpecs

__version__ = "0.1.0"
__all__ = [
    # Modules
    "api",
    "io", 
    "info",
    "status",
    # Types
    "FileType",
    "Status",
    # Session
    "session",
    # API classes
    "API",
    "JobAPI",
    "AccessToken",
    "AccessTokenFixed", 
    "AccessTokenAuth",
    # Model classes
    "JobSpecs",
    "HardwareSpecs",
    "AppSpecs",
    "HandlerSpecs",
    "MetaSpecs",
]
