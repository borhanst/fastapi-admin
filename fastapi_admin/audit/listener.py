"""Audit listener — SQLAlchemy after_flush event listener for audit logging."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from fastapi_admin.audit.models import AuditLog


def compute_diff(old_values: dict[str, Any], new_values: dict[str, Any]) -> dict[str, Any]:
    """Compute the diff between old and new values."""
    diff = {}
    all_keys = set(old_values.keys()) | set(new_values.keys())

    for key in all_keys:
        old_val = old_values.get(key)
        new_val = new_values.get(key)
        if old_val != new_val:
            diff[key] = {"old": old_val, "new": new_val}

    return diff


def get_audit_context(session: Session) -> dict[str, Any]:
    """Extract audit context (user info, IP, etc.) from the session."""
    # This will be populated by middleware or explicit setting
    return getattr(session, "_audit_context", {})


def setup_audit_listener(session_factory: Any, exclude_tables: list[str] | None = None) -> None:
    """Set up the SQLAlchemy event listener for audit logging.

    Args:
        session_factory: The async session factory
        exclude_tables: Tables to exclude from audit logging
    """
    exclude = set(exclude_tables or [])
    exclude.add(AuditLog.__table__.name)  # Never audit the audit log itself

    @event.listens_for(Session, "after_flush")
    def after_flush(session: Session, flush_context: Any) -> None:
        """Log all INSERT, UPDATE, DELETE operations after flush."""
        context = get_audit_context(session)
        user_id = context.get("user_id")
        username = context.get("username")
        ip_address = context.get("ip_address")
        user_agent = context.get("user_agent")

        # Process new objects (INSERT)
        for obj in session.new:
            table_name = obj.__tablename__
            if table_name in exclude:
                continue

            # Get primary key
            pk_value = getattr(obj, "id", None)
            if pk_value is None:
                for col in obj.__table__.primary_key.columns:
                    pk_value = getattr(obj, col.key, None)
                    break

            # Get all column values
            new_values = {}
            for col in obj.__table__.columns:
                val = getattr(obj, col.key, None)
                # Convert non-serializable types
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                elif hasattr(val, "hex"):
                    val = str(val)
                new_values[col.key] = val

            audit_entry = AuditLog(
                table_name=table_name,
                record_id=str(pk_value),
                action="CREATE",
                user_id=user_id,
                username=username,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(audit_entry)

        # Process modified objects (UPDATE)
        for obj, changes in session.dirty.items():
            table_name = obj.__tablename__
            if table_name in exclude:
                continue

            # Get primary key
            pk_value = getattr(obj, "id", None)
            if pk_value is None:
                for col in obj.__table__.primary_key.columns:
                    pk_value = getattr(obj, col.key, None)
                    break

            # Compute old and new values for changed columns
            old_values = {}
            new_values = {}
            for col_name in changes:
                col = obj.__table__.columns.get(col_name)
                if col is None:
                    continue

                # History has the committed state
                history = session.identity_map.get(obj._sa_instance_state.key)
                if history:
                    old_val = getattr(history, col_name, None)
                else:
                    old_val = None

                new_val = getattr(obj, col_name, None)

                # Convert non-serializable types
                if hasattr(old_val, "isoformat"):
                    old_val = old_val.isoformat()
                elif hasattr(old_val, "hex"):
                    old_val = str(old_val)

                if hasattr(new_val, "isoformat"):
                    new_val = new_val.isoformat()
                elif hasattr(new_val, "hex"):
                    new_val = str(new_val)

                old_values[col_name] = old_val
                new_values[col_name] = new_val

            diff = compute_diff(old_values, new_values)

            audit_entry = AuditLog(
                table_name=table_name,
                record_id=str(pk_value),
                action="UPDATE",
                user_id=user_id,
                username=username,
                old_values=old_values,
                new_values=new_values,
                diff=diff,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(audit_entry)

        # Process deleted objects (DELETE)
        for obj in session.deleted:
            table_name = obj.__tablename__
            if table_name in exclude:
                continue

            # Get primary key
            pk_value = getattr(obj, "id", None)
            if pk_value is None:
                for col in obj.__table__.primary_key.columns:
                    pk_value = getattr(obj, col.key, None)
                    break

            # Get all column values before deletion
            old_values = {}
            for col in obj.__table__.columns:
                val = getattr(obj, col.key, None)
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                elif hasattr(val, "hex"):
                    val = str(val)
                old_values[col.key] = val

            audit_entry = AuditLog(
                table_name=table_name,
                record_id=str(pk_value),
                action="DELETE",
                user_id=user_id,
                username=username,
                old_values=old_values,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(audit_entry)
