"""Audit listener — SQLAlchemy event listeners for audit logging."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from fastapi_console.audit.context import clear_audit_context, get_audit_context
from fastapi_console.audit.diff import compute_diff, snapshot
from fastapi_console.audit.models import AuditLog


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


def attach_audit_listener(session_factory: Any, registry: Any) -> None:
    """Set up SQLAlchemy event listeners for audit logging.
    
    Args:
        session_factory: The session factory (sync or async)
        registry: The AdminRegistry instance
    """
    # We'll attach to the Session class (works for both sync and async)
    @event.listens_for(Session, "before_flush")
    def before_flush(session: Session, flush_context: Any, instances: Any) -> None:
        """Before flush, snapshot the original state of dirty objects for UPDATE."""
        # For each dirty object, take a snapshot and store it on the object
        for obj in session.dirty:
            if not is_registered_model(obj, registry):
                continue
            # Skip if it's the audit log itself
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            # Snapshot the current state (from the database) as the "before" state
            # We'll store it on the object for use in after_flush
            obj._audit_before = snapshot(obj)

    @event.listens_for(Session, "after_flush")
    def after_flush(session: Session, flush_context: Any) -> None:
        """After flush, create audit log entries for CREATE, UPDATE, DELETE."""
        # Get audit context from contextvar
        context = get_audit_context()
        user_id = context.get("user_id")
        user_email = context.get("user_email")
        ip_address = context.get("ip_address")
        user_agent = context.get("user_agent")

        # Process new objects (INSERT)
        for obj in session.new:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            # Snapshot the object after flush (it should have its ID now)
            after_snapshot = snapshot(obj)
            audit_entry = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action="CREATE",
                model_name=obj.__class__.__name__,
                table_name=obj.__tablename__,
                object_id=str(getattr(obj, "id")),
                object_repr=str(obj)[:255],  # Truncate if needed
                changes=None,  # CREATE has no diff
                full_snapshot=after_snapshot,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(audit_entry)

        # Process dirty objects (UPDATE)
        for obj in session.dirty:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            # Check if we have a before snapshot
            if not hasattr(obj, "_audit_before"):
                # This can happen if the object was made dirty in this session
                # but we didn't have a chance to snapshot in before_flush (e.g., if it was
                # added and then modified in the same flush). We'll skip for simplicity.
                continue
            before_snapshot = getattr(obj, "_audit_before")
            after_snapshot = snapshot(obj)
            diff = compute_diff(before_snapshot, after_snapshot)
            # Skip if no changes (except maybe the audit fields? but we don't track those)
            if not diff:
                # Clean up the temporary attribute
                del obj._audit_before
                continue
            audit_entry = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action="UPDATE",
                model_name=obj.__class__.__name__,
                table_name=obj.__tablename__,
                object_id=str(getattr(obj, "id")),
                object_repr=str(obj)[:255],
                changes=diff,  # The diff of changed fields
                full_snapshot=after_snapshot,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(audit_entry)
            # Clean up the temporary attribute
            del obj._audit_before

        # Process deleted objects (DELETE)
        for obj in session.deleted:
            if not is_registered_model(obj, registry):
                continue
            if obj.__tablename__ == AuditLog.__tablename__:
                continue
            # Snapshot the object before it's gone
            before_snapshot = snapshot(obj)
            audit_entry = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action="DELETE",
                model_name=obj.__class__.__name__,
                table_name=obj.__tablename__,
                object_id=str(getattr(obj, "id")),
                object_repr=str(obj)[:255],
                changes=None,  # DELETE has no diff
                full_snapshot=before_snapshot,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(audit_entry)

    # We don't need to clear the context here because the middleware will do it.
    # But we can add an event for after_commit or after_rollback to clear the context
    # if we want to be safe. However, the middleware should clear it after the response.


# We'll also provide a function to clear the audit context (used by middleware)
def clear_audit_context_after_response() -> None:
    """Clear the audit context (to be called after the response is sent)."""
    clear_audit_context()