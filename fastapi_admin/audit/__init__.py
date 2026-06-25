"""Audit module — AuditLog model, SQLAlchemy event listener, diff, context, middleware."""

from __future__ import annotations

from fastapi_admin.audit.context import (
    AuditContext,
    clear_audit_context,
    get_audit_context,
    set_audit_context,
)
from fastapi_admin.audit.diff import compute_diff, snapshot
from fastapi_admin.audit.events import AuditEvent
from fastapi_admin.audit.event_bus import AuditEventBus
from fastapi_admin.audit.listener import (
    attach_audit_listener,
    is_registered_model,
)
from fastapi_admin.audit.logger import AuditLogger
from fastapi_admin.audit.models import AuditLog
from fastapi_admin.audit.middleware import audit_context_middleware
from fastapi_admin.audit.sqlalchemy_logger import SqlAlchemyAuditLogger

__all__ = [
    "AuditContext",
    "AuditEvent",
    "AuditEventBus",
    "AuditLog",
    "AuditLogger",
    "SqlAlchemyAuditLogger",
    "attach_audit_listener",
    "audit_context_middleware",
    "clear_audit_context",
    "compute_diff",
    "get_audit_context",
    "is_registered_model",
    "set_audit_context",
    "snapshot",
]
