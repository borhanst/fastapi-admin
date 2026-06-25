"""ModelAdmin base class — configuration + lifecycle hooks + validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi_console.types import ExtraField, FieldMeta

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from fastapi_console.nav import NavItemConfig


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
    list_filter_options: dict[str, dict[str, Any]] = {}
    list_filter_horizontal: bool = False

    # Actions config
    actions_list: list[str] = []
    actions_row: list[str] = []
    actions_detail: list[str] = []
    actions_submit_line: list[str] = []
    actions_list_hide_default: bool = False

    # Form config
    fields: list[str] | None = None
    exclude: list[str] | None = None
    readonly_fields: list[str] | None = None
    formfield_overrides: dict[str, Any] = {}
    extra_fields: list[ExtraField] = []
    fieldsets: list[
        Any
    ] = []  # FieldsetSpec accepted but not strictly enforced here
    field_placeholders: dict[str, str] = {}  # {field_name: placeholder_text}

    # Conditional fields
    conditional_fields: dict[str, dict[str, Any]] = {}

    # Form UX config
    warn_unsaved_form: bool = True
    compressed_fields: bool = True
    change_form_show_cancel_button: bool = True

    # Labels and display
    verbose_name: str | None = None
    verbose_name_plural: str | None = None
    icon: str | None = None
    tag: str | None = None
    tags: list[str] | None = None
    nav_order: int = 999
    nav_children: list[NavItemConfig] | None = None

    # Badge hook — return str e.g. "12" or None
    def get_nav_badge(self, request: Any = None) -> str | None:
        return None

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

    def on_update(
        self, obj: Any, data: dict[str, Any], request: Any = None
    ) -> None:
        """Called before UPDATE. *data* contains the incoming form values."""

    def after_update(self, obj: Any, request: Any = None) -> None:
        """Called after UPDATE commit."""

    def on_delete(self, obj: Any, request: Any = None) -> None:
        """Called before DELETE."""

    def after_delete(self, obj: Any, request: Any = None) -> None:
        """Called after DELETE commit."""

    # ── Validation hooks (stubs) ────────────────────────────────────

    def validate_create(
        self, data: dict[str, Any], request: Any = None
    ) -> dict[str, Any]:
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
        from fastapi_console.inspection import auto_label, is_required

        columns = columns or []
        relationships = relationships or []
        form_fields: list[FieldMeta] = []

        raw = []
        if self.fields is not None:
            names = set(self.fields)
            raw = [
                c for c in columns if c.name in names and not c.primary_key
            ] + [
                r
                for r in relationships
                if r.name in names
                and r.direction in ("MANYTOONE", "MANYTOMANY")
            ]
        else:
            raw = [c for c in columns if not c.primary_key] + [
                r
                for r in relationships
                if r.direction in ("MANYTOONE", "MANYTOMANY")
            ]
            if self.exclude:
                raw = [x for x in raw if x.name not in self.exclude]

        for item in raw:
            name = item.name
            readonly = name in (self.readonly_fields or [])
            required = is_required(item) if hasattr(item, "nullable") else False
            label = auto_label(name)
            placeholder = self.field_placeholders.get(
                name, f"Enter {label.lower()}..."
            )
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

    # ── Action helpers ─────────────────────────────────────────────

    def get_actions_for_location(self, location: str) -> list[Any]:
        """Get resolved Action instances for a given location (list/row/detail/submit_line)."""
        from fastapi_console.actions.base import Action

        action_names = getattr(self, f"actions_{location}", [])
        resolved = []
        for name in action_names:
            action_fn = getattr(self, name, None)
            if not action_fn:
                continue
            if hasattr(action_fn, "_admin_action"):
                resolved.append(action_fn._admin_action())
            elif callable(action_fn):
                label = name.replace("_", " ").title()
                _fn = action_fn
                _admin = self

                class _FallbackAction(Action):
                    def __init__(self):
                        super().__init__(name=name, label=label)

                    async def execute(self, objects, request):
                        import inspect

                        if inspect.iscoroutinefunction(_fn):
                            await _fn(_admin, objects, request)
                        else:
                            _fn(_admin, objects, request)

                resolved.append(_FallbackAction())
        return resolved

    def get_list_actions(self) -> list[Any]:
        return self.get_actions_for_location("list")

    def get_row_actions(self) -> list[Any]:
        return self.get_actions_for_location("row")

    def get_detail_actions(self) -> list[Any]:
        return self.get_actions_for_location("detail")

    def get_submit_line_actions(self) -> list[Any]:
        return self.get_actions_for_location("submit_line")

    # ── Permission helpers ───────────────────────────────────────────

    def has_view_permission(self, request: Any = None) -> bool:
        return True

    def has_create_permission(self, request: Any = None) -> bool:
        return True

    def has_edit_permission(self, request: Any = None) -> bool:
        return True

    def has_delete_permission(self, request: Any = None) -> bool:
        return True
