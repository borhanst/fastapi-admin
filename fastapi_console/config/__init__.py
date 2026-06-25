"""Configuration classes for FastAPI Console."""

from fastapi_console.config.audit import AuditConfig
from fastapi_console.config.auth import AuthConfig
from fastapi_console.config.behavior import BehaviorConfig
from fastapi_console.config.nav import NavConfig
from fastapi_console.config.storage import StorageConfig
from fastapi_console.config.theme import ThemeConfig
from fastapi_console.config.ui import UIConfig

__all__ = [
    "AuthConfig",
    "AuditConfig",
    "UIConfig",
    "BehaviorConfig",
    "StorageConfig",
    "NavConfig",
    "ThemeConfig",
]
