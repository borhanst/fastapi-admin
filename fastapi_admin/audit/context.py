"""Audit context — thread-local storage for audit information."""

from __future__ import annotations

from contextvars import ContextVar

# Context variable to store audit context (user, IP, user_agent, etc.)
_current_audit_context: ContextVar[dict] = ContextVar("_current_audit_context", default={})


def get_audit_context() -> dict:
    """Get the current audit context."""
    return _current_audit_context.get()


def set_audit_context(data: dict) -> None:
    """Set the audit context (merges with existing)."""
    current = get_audit_context()
    current.update(data)
    _current_audit_context.set(current)


def clear_audit_context() -> None:
    """Clear the audit context."""
    _current_audit_context.set({})