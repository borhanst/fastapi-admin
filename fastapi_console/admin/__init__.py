"""Admin component classes for FastAPI Console."""

from fastapi_console.admin.admin_config import AdminConfig
from fastapi_console.admin.admin_database import AdminDatabase
from fastapi_console.admin.admin_router import AdminRouter
from fastapi_console.admin.admin_template import AdminTemplate
from fastapi_console.admin.core import Admin
from fastapi_console.admin.state import AdminState

__all__ = [
    "Admin",
    "AdminConfig",
    "AdminDatabase",
    "AdminRouter",
    "AdminState",
    "AdminTemplate",
]
