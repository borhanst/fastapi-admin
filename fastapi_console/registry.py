"""AdminRegistry — singleton holding all registered models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fastapi_console.inspection import ColumnMeta, RelationMeta, inspect_model

if TYPE_CHECKING:
    from fastapi_console.views import ModelAdmin
    from fastapi_console.widgets.base import Widget


@dataclass
class RegisteredModel:
    """Central dataclass holding a registered model and its admin config."""

    model: type
    admin: "ModelAdmin"
    table_name: str
    verbose_name: str
    verbose_name_plural: str
    columns: list[ColumnMeta] = field(default_factory=list)
    relationships: list[RelationMeta] = field(default_factory=list)
    pk_field: str = "id"

    def __post_init__(self) -> None:
        # Find primary key
        for col in self.columns:
            if col.primary_key:
                self.pk_field = col.name
                break

    @property
    def form_fields(self) -> list[Any]:
        return self.admin.get_form_fields(
            columns=self.columns,
            relationships=self.relationships,
        )

    @property
    def list_fields(self) -> list[str]:
        if self.admin.list_display:
            valid = {c.name for c in self.columns}
            return [f for f in self.admin.list_display if f in valid]
        return [c.name for c in self.columns if not c.primary_key]

    def get_widget(self, field_name: str) -> "Widget":
        from fastapi_console.widgets.registry import widget_registry
        from fastapi_console.inspection import auto_label
        from fastapi_console.widgets.relation import (
            RelationPickerWidget,
            MultiRelationWidget,
        )

        col = next((c for c in self.columns if c.name == field_name), None)
        rel = next((r for r in self.relationships if r.name == field_name), None)
        if col is not None:
            widget = widget_registry.resolve(col)
            if isinstance(widget, RelationPickerWidget) and not widget.related_table and col.foreign_keys:
                fk = col.foreign_keys[0]
                widget.related_table = fk.column.table.name
            return widget
        if rel is not None:
            related_verbose = auto_label(
                rel.target_model.__tablename__
            )
            if rel.direction == "MANYTOONE" or not rel.uselist:
                return RelationPickerWidget(
                    related_table=rel.target_model.__tablename__,
                    related_verbose=related_verbose,
                )
            return MultiRelationWidget(
                related_table=rel.target_model.__tablename__,
                related_verbose=related_verbose,
            )
        return widget_registry.resolve(  # type: ignore[arg-type]
            type("_Col", (), {"type": type(None), "name": field_name})()
        )


class AdminRegistry:
    """Singleton registry for admin models."""

    _instance: AdminRegistry | None = None
    _models: dict[str, RegisteredModel] = {}

    def __new__(cls) -> AdminRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
        return cls._instance

    def register(
        self,
        model: type,
        admin_class: type[ModelAdmin] | None = None,
    ) -> RegisteredModel:
        """Register a model with the admin."""
        from fastapi_console.views import ModelAdmin

        if not hasattr(model, "__tablename__"):
            raise ValueError(
                f"{model.__name__} is not a SQLAlchemy model (no __tablename__)"
            )

        admin = admin_class() if admin_class else ModelAdmin()
        columns, relationships = inspect_model(model)

        table_name = model.__tablename__
        verbose_name = admin.verbose_name or table_name.replace("_", " ").title()
        if admin.verbose_name_plural:
            verbose_name_plural = admin.verbose_name_plural
        elif verbose_name.endswith("y") and len(verbose_name) > 1 and verbose_name[-2].lower() not in "aeiou":
            verbose_name_plural = f"{verbose_name[:-1]}ies"
        else:
            verbose_name_plural = f"{verbose_name}s"

        registered = RegisteredModel(
            model=model,
            admin=admin,
            table_name=table_name,
            verbose_name=verbose_name,
            verbose_name_plural=verbose_name_plural,
            columns=columns,
            relationships=relationships,
        )

        self._models[table_name] = registered
        return registered

    def get(self, table_name: str) -> RegisteredModel | None:
        """Get a registered model by table name."""
        return self._models.get(table_name)

    def all(self) -> list[RegisteredModel]:
        """Get all registered models."""
        return list(self._models.values())

    def auto_discover(self) -> list[RegisteredModel]:
        """Scan all subclasses of DeclarativeBase and register unregistered ones."""
        from sqlalchemy.orm import DeclarativeBase

        discovered: list[RegisteredModel] = []
        seen: set[type] = set()
        for subclass in _all_declarative_subclasses(DeclarativeBase):
            if hasattr(subclass, "registry"):
                for mapper in subclass.registry.mappers:
                    cls = mapper.class_
                    if cls not in seen:
                        seen.add(cls)
                        if hasattr(cls, "__tablename__") and cls.__tablename__ not in self._models:
                            discovered.append(self.register(cls))
        return discovered

    def clear(self) -> None:
        """Clear all registrations (useful for testing)."""
        self._models.clear()


def _all_declarative_subclasses(base: type) -> set[type]:
    """Recursively collect all subclasses of *base*."""
    result: set[type] = set()
    work = [base]
    while work:
        cls = work.pop()
        for sub in cls.__subclasses__():
            if sub not in result:
                result.add(sub)
                work.append(sub)
    return result
