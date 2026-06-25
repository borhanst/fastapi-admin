"""Configuration classes for FastAPI Admin."""

from fastapi_admin.config.audit import AuditConfig
from fastapi_admin.config.auth import AuthConfig
from fastapi_admin.config.behavior import BehaviorConfig
from fastapi_admin.config.nav import NavConfig
from fastapi_admin.config.storage import StorageConfig
from fastapi_admin.config.ui import UIConfig

__all__ = [
    "AuthConfig",
    "AuditConfig",
    "UIConfig",
    "BehaviorConfig",
    "StorageConfig",
    "NavConfig",
]