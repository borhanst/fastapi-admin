"""ModelAdmin base class — configuration + lifecycle hooks + validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi_admin.types import ExtraField, FieldMeta

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
    formfield_overrides: dict[str, Any] = {}
    extra_fields: list[ExtraField] = []
    fieldsets: list[Any] = []  # FieldsetSpec accepted but not strictly enforced here
    field_placeholders: dict[str, str] = {}  # {field_name: placeholder_text}

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

    def get_model(self) -> Any:
        return self.model

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

    # ── Form field helper ───────────────────────────────────────────

    def get_form_fields(
        self,
        obj: Any = None,
        request: Any = None,
        columns: list[Any] | None = None,
        relationships: list[Any] | None = None,
    ) -> list[FieldMeta]:
        """Return ordered list of FieldMeta objects for the create/edit form."""
        from fastapi_admin.inspection import auto_label, is_required

        columns = columns or []
        relationships = relationships or []
        form_fields: list[FieldMeta] = []

        raw = []
        if self.fields is not None:
            names = set(self.fields)
            raw = [c for c in columns if c.name in names and not c.primary_key] + [
                r for r in relationships if r.name in names and r.direction in ("MANYTOONE", "MANYTOMANY")
            ]
        else:
            raw = [c for c in columns if not c.primary_key] + [
                r for r in relationships if r.direction in ("MANYTOONE", "MANYTOMANY")
            ]
            if self.exclude:
                raw = [x for x in raw if x.name not in self.exclude]

        for item in raw:
            name = item.name
            readonly = name in (self.readonly_fields or [])
            required = is_required(item) if hasattr(item, "nullable") else False
            label = auto_label(name)
            placeholder = self.field_placeholders.get(name, f"Enter {label.lower()}...")
            form_fields.append(
                FieldMeta(
                    name=name,
                    label=label,
                    required=required,
                    readonly=readonly,
                    placeholder=placeholder,
                )
            )

        for extra in self.extra_fields:
            form_fields.append(
                FieldMeta(
                    name=extra.name,
                    label=extra.label or auto_label(extra.name),
                    required=extra.required,
                    readonly=True,
                    extra={"extra_field": True, "widget": extra.widget},
                )
            )

        # Respect fieldsets ordering if defined
        if self.fieldsets:
            ordered: list[FieldMeta] = []
            seen: set[str] = set()
            for fs in self.fieldsets:
                for fname in fs.fields:
                    for fm in form_fields:
                        if fm.name == fname and fname not in seen:
                            ordered.append(fm)
                            seen.add(fname)
                            break
            for fm in form_fields:
                if fm.name not in seen:
                    ordered.append(fm)
            return ordered

        return form_fields

    # ── Permission helpers ───────────────────────────────────────────

    def has_view_permission(self, request: Any = None) -> bool:
        return True

    def has_create_permission(self, request: Any = None) -> bool:
        return True

    def has_edit_permission(self, request: Any = None) -> bool:
        return True

    def has_delete_permission(self, request: Any = None) -> bool:
        return True