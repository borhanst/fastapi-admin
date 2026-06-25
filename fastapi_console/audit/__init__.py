"""Audit module — AuditLog model, SQLAlchemy event listener, diff, context, middleware."""

from __future__ import annotations

from fastapi_console.audit.context import (
    clear_audit_context,
    get_audit_context,
    set_audit_context,
)
from fastapi_console.audit.diff import compute_diff, snapshot
from fastapi_console.audit.listener import (
    attach_audit_listener,
    is_registered_model,
)
from fastapi_console.audit.middleware import audit_context_middleware
from fastapi_console.audit.models import AuditLog

__all__ = [
    "AuditLog",
    "attach_audit_listener",
    "clear_audit_context",
    "compute_diff",
    "get_audit_context",
    "is_registered_model",
    "set_audit_context",
    "snapshot",
    "audit_context_middleware",
]