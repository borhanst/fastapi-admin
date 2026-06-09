"""ModelAdmin base class — configuration + lifecycle hooks + validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ModelAdmin:
    """Base class for model admin configuration.

    Subclass this to customise how a model is displayed, filtered, and edited.
    All fields are optional — unset fields fall back to auto-detected values.
    """

    # List view config
    list_display: list[str] | None = None
    list_filter: list[str] | None = None
    search_fields: list[str] | None = None
    ordering: list[str] | None = None
    per_page: int = 20

    # Form config
    fields: list[str] | None = None
    exclude: list[str] | None = None
    readonly_fields: list[str] | None = None

    # Labels and display
    verbose_name: str | None = None
    verbose_name_plural: str | None = None
    icon: str | None = None

    # Object display
    def __str__(self, obj: Any) -> str:
        """How to display an object in dropdowns/links."""
        return str(
            getattr(obj, "name", None)
            or getattr(obj, "title", None)
            or f"#{getattr(obj, 'id', '?')}"
        )

    # ── Query hooks ──────────────────────────────────────────────────

    def get_queryset(self, session: Session, request: Any = None) -> Any:
        """Override to filter records globally (e.g. soft-delete filter)."""
        return session.query(self.model)  # type: ignore[attr-defined]

    def get_object(self, session: Session, id: Any) -> Any:
        """Override for custom PK lookup."""
        return session.get(self.model, id)  # type: ignore[attr-defined]

    # ── Lifecycle hooks (stubs) ─────────────────────────────────────

    def on_create(self, obj: Any, request: Any = None) -> None:
        """Called before INSERT. Mutate *obj* as needed."""

    def after_create(self, obj: Any, request: Any = None) -> None:
        """Called after INSERT commit."""

    def on_update(self, obj: Any, data: dict[str, Any], request: Any = None) -> None:
        """Called before UPDATE. *data* contains the incoming form values."""

    def after_update(self, obj: Any, request: Any = None) -> None:
        """Called after UPDATE commit."""

    def on_delete(self, obj: Any, request: Any = None) -> None:
        """Called before DELETE."""

    def after_delete(self, obj: Any, request: Any = None) -> None:
        """Called after DELETE commit."""

    # ── Validation hooks (stubs) ────────────────────────────────────

    def validate_create(self, data: dict[str, Any], request: Any = None) -> dict[str, Any]:
        """Validate and/or transform form data before create.

        Return the (possibly modified) data dict.  Raise ``ValueError``
        with a user-facing message to abort the operation.
        """
        return data

    def validate_update(
        self, obj: Any, data: dict[str, Any], request: Any = None
    ) -> dict[str, Any]:
        """Validate and/or transform form data before update.

        Return the (possibly modified) data dict.  Raise ``ValueError``
        with a user-facing message to abort the operation.
        """
        return data

    # ── Permission helpers ───────────────────────────────────────────

    def has_view_permission(self, request: Any = None) -> bool:
        return True

    def has_create_permission(self, request: Any = None) -> bool:
        return True

    def has_edit_permission(self, request: Any = None) -> bool:
        return True

    def has_delete_permission(self, request: Any = None) -> bool:
        return True
