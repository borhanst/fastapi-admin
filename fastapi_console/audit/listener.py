"""Audit listener — SQLAlchemy event listeners that publish audit events."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import instance_state

from fastapi_console.audit.context import get_audit_context
from fastapi_console.audit.diff import compute_diff, serialize_value, snapshot
from fastapi_console.audit.event_bus import AuditEventBus
from fastapi_console.audit.models import AuditLog
from fastapi_console.audit.sqlalchemy_logger import SqlAlchemyAuditLogger

_audit_logger: SqlAlchemyAuditLogger | None = None


def is_registered_model(obj: Any, registry: Any) -> bool:
    """Check if a model class is registered with the admin."""
    if not hasattr(obj, "__tablename__"):
        return False
    table_name = getattr(obj, "__tablename__")
    return registry.get(table_name) is not None


def _snapshot_from_committed(obj: Any) -> dict[str, Any]:
    """Snapshot column values from the committed (pre-flush) state.

    Uses the SQLAlchemy pending history to read the *old* values that
    were in the database before the current pending changes, avoiding
    any attribute access that would trigger lazy-load I/O.
    """
    if not hasattr(obj, "__table__"):
        return {}
    mapper = instance_state(obj).manager.mapper
    data: dict[str, Any] = {}
    for column in mapper.columns:
        attr = instance_state(obj).attrs[column.key]
        # history.added / history.unchanged / history.deleted
        # For a dirty attribute: deleted = old value, added = new value
        history = attr.history
        if history.deleted:
            data[column.key] = serialize_value(history.deleted[0])
        elif history.unchanged:
            data[column.key] = serialize_value(history.unchanged[0])
        else:
            # No history — fall back to current value (e.g. server_default)
            data[column.key] = serialize_value(getattr(obj, column.key))
    return data


def attach_audit_listener(
    session_factory: Any,
    registry: Any,
    bus: AuditEventBus | None = None,
) -> AuditEventBus:
    """Set up SQLAlchemy event listeners for audit logging.

    Args:
        session_factory: The session factory (sync or async)
        registry: The AdminRegistry instance
        bus: Optional pre-configured AuditEventBus.

    Returns:
        The AuditEventBus instance
    """
    global _audit_logger

    if bus is None:
        bus = AuditEventBus()

    if _audit_logger is None:
        _audit_logger = SqlAlchemyAuditLogger()
        bus.subscribe("CREATE", _audit_logger.log_create)
        bus.subscribe("UPDATE", _audit_logger.log_update)
        bus.subscribe("DELETE", _audit_logger.log_delete)

    @event.listens_for(Session, "before_flush")
    def before_flush(session: Session, flush_context: Any, instances: Any) -> None:
        """Capture before/after states for all tracked objects.

        Both snapshots are taken here — while attributes are still loaded
        — so that ``after_flush`` never touches the (now-expired) objects.
        """
        # Dirty objects → snapshot both committed (before) and pending (after)
        for obj in session.dirty:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            obj._audit_before = _snapshot_from_committed(obj)
            obj._audit_after = snapshot(obj)

        # New objects → only an after-snapshot (no before state)
        for obj in session.new:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            obj._audit_after = snapshot(obj)

    @event.listens_for(Session, "after_flush")
    def after_flush(session: Session, flush_context: Any) -> None:
        """Build AuditEvents using pre-computed snapshots.

        No attribute access on the ORM objects here — all data was
        captured in ``before_flush`` to avoid MissingGreenlet errors
        with async sessions (expired attributes → greenlet_spawn).
        """
        context = get_audit_context()

        # INSERT
        for obj in session.new:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            after = getattr(obj, "_audit_after", None)
            if after is None:
                after = {}
            bus.emit_for_object(obj, "CREATE", context, snapshot_data=after)

        # UPDATE
        for obj in session.dirty:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            before = getattr(obj, "_audit_before", None)
            after = getattr(obj, "_audit_after", None)
            if before is None or after is None:
                continue
            diff = compute_diff(before, after)
            del obj._audit_before
            del obj._audit_after
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


async def flush_audit_entries(session: Any) -> None:
    """Flush any buffered audit log entries to the database."""
    if _audit_logger is not None:
        await _audit_logger.flush_pending(session)


def clear_audit_context_after_response() -> None:
    """Clear the audit context (to be called after the response is sent)."""
    from fastapi_console.audit.context import clear_audit_context
    clear_audit_context()
