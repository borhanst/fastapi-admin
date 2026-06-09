"""Audit module — AuditLog model, SQLAlchemy event listener, diff, context."""

from __future__ import annotations

from fastapi_admin.audit.models import AuditLog

__all__ = ["AuditLog"]
