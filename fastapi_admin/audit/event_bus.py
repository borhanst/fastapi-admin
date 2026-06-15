"""Audit event bus — publish/subscribe system for audit events."""

from __future__ import annotations

from typing import Any, Callable

from fastapi_admin.audit.events import AuditEvent
from fastapi_admin.audit.diff import snapshot, compute_diff


class AuditEventBus:
    """Central event bus for audit events.

    The listener publishes events here. Loggers and other subscribers
    consume them. This decouples the SQLAlchemy event hooks from the
    audit logging implementation.
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[AuditEvent], None]]] = {
            "CREATE": [],
            "UPDATE": [],
            "DELETE": [],
        }

    def subscribe(self, event_type: str, listener: Callable[[AuditEvent], None]) -> None:
        """Register a listener for a specific event type.

        Args:
            event_type: "CREATE", "UPDATE", or "DELETE"
            listener: Callable that receives an AuditEvent
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def publish(self, event: AuditEvent) -> None:
        """Publish an event to all listeners of its type.

        Args:
            event: The AuditEvent to publish
        """
        for listener in self._listeners.get(event.event_type, []):
            listener(event)

    def emit_for_object(
        self,
        obj: Any,
        event_type: str,
        context: dict[str, Any],
        changes: dict[str, Any] | None = None,
    ) -> None:
        """Build an AuditEvent from a SQLAlchemy object and publish it.

        Args:
            obj: The SQLAlchemy model instance
            event_type: "CREATE", "UPDATE", or "DELETE"
            context: Audit context dict with user_id, user_email, ip_address, user_agent
            changes: Pre-computed diff (used for UPDATE; ignored for CREATE/DELETE)
        """
        obj_snapshot = snapshot(obj)

        if event_type == "UPDATE" and changes is not None:
            event_changes = changes
        else:
            event_changes = None

        event = AuditEvent(
            event_type=event_type,
            model_name=obj.__class__.__name__,
            table_name=obj.__tablename__,
            object_id=str(getattr(obj, "id")),
            object_repr=str(obj)[:255],
            changes=event_changes,
            full_snapshot=obj_snapshot,
            user_id=context.get("user_id"),
            user_email=context.get("user_email"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
        )
        self.publish(event)
