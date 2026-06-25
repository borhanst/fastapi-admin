"""Audit listener — SQLAlchemy event listeners that publish audit events."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from fastapi_admin.audit.context import get_audit_context
from fastapi_admin.audit.diff import compute_diff, snapshot
from fastapi_admin.audit.event_bus import AuditEventBus
from fastapi_admin.audit.models import AuditLog
from fastapi_admin.audit.sqlalchemy_logger import SqlAlchemyAuditLogger


def is_registered_model(obj: Any, registry: Any) -> bool:
    """Check if a model class is registered with the admin.

    Args:
        obj: A SQLAlchemy model instance
        registry: The AdminRegistry instance

    Returns:
        True if the model is registered, False otherwise
    """
    if not hasattr(obj, "__tablename__"):
        return False
    table_name = getattr(obj, "__tablename__")
    return registry.get(table_name) is not None


def attach_audit_listener(
    session_factory: Any,
    registry: Any,
    bus: AuditEventBus | None = None,
) -> AuditEventBus:
    """Set up SQLAlchemy event listeners for audit logging.

    Args:
        session_factory: The session factory (sync or async)
        registry: The AdminRegistry instance
        bus: Optional pre-configured AuditEventBus. If None, a new one
             is created with a SqlAlchemyAuditLogger wired to the session.

    Returns:
        The AuditEventBus instance (so callers can subscribe additional listeners)
    """
    if bus is None:
        bus = AuditEventBus()

    # Wire up the default DB logger if not already subscribed
    _has_db_logger = any(
        isinstance(ln, SqlAlchemyAuditLogger)
        for listeners in bus._listeners.values()
        for ln in listeners
    )

    @event.listens_for(Session, "before_flush")
    def before_flush(session: Session, flush_context: Any, instances: Any) -> None:
        """Snapshot the original state of dirty objects for UPDATE diffs."""
        for obj in session.dirty:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            obj._audit_before = snapshot(obj)

    @event.listens_for(Session, "after_flush")
    def after_flush(session: Session, flush_context: Any) -> None:
        """Build AuditEvents and publish them to the bus."""
        context = get_audit_context()

        # INSERT
        for obj in session.new:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            bus.emit_for_object(obj, "CREATE", context)

        # UPDATE
        for obj in session.dirty:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            if not hasattr(obj, "_audit_before"):
                continue
            before_snapshot = getattr(obj, "_audit_before")
            after_snapshot = snapshot(obj)
            diff = compute_diff(before_snapshot, after_snapshot)
            del obj._audit_before
            if not diff:
                continue
            bus.emit_for_object(obj, "UPDATE", context, changes=diff)

        # DELETE
        for obj in session.deleted:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            bus.emit_for_object(obj, "DELETE", context)

    return bus


def clear_audit_context_after_response() -> None:
    """Clear the audit context (to be called after the response is sent)."""
    from fastapi_admin.audit.context import clear_audit_context
    clear_audit_context()
