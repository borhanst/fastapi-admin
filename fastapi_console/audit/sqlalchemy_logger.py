"""SQLAlchemy audit logger — persists audit events to the database."""

from __future__ import annotations

from typing import Any

from fastapi_console.audit.events import AuditEvent
from fastapi_console.audit.logger import AuditLogger
from fastapi_console.audit.models import AuditLog


class SqlAlchemyAuditLogger(AuditLogger):
    """Writes AuditEvents to the admin_audit_log table.

    This is the concrete adapter that bridges the event system
    to the database. It receives AuditEvent objects and writes
    them as AuditLog rows.
    """

    def __init__(self, session: Any) -> None:
        self._session = session

    def log_create(self, event: AuditEvent) -> None:
        self._write(event)

    def log_update(self, event: AuditEvent) -> None:
        self._write(event)

    def log_delete(self, event: AuditEvent) -> None:
        self._write(event)

    def _write(self, event: AuditEvent) -> None:
        entry = AuditLog(
            user_id=event.user_id,
            user_email=event.user_email,
            action=event.event_type,
            model_name=event.model_name,
            table_name=event.table_name,
            object_id=event.object_id,
            object_repr=event.object_repr,
            changes=event.changes,
            full_snapshot=event.full_snapshot,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
        )
        self._session.add(entry)
