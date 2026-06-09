"""AdminRegistry — singleton holding all registered models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fastapi_admin.inspection import ColumnMeta, RelationMeta, inspect_model

if TYPE_CHECKING:
    from fastapi_admin.views import ModelAdmin


@dataclass
class RegisteredModel:
    """Central dataclass holding a registered model and its admin config."""

    model: type
    admin: ModelAdmin
    table_name: str
    verbose_name: str
    verbose_name_plural: str
    columns: list[ColumnMeta] = field(default_factory=list)
    relationships: list[RelationMeta] = field(default_factory=list)
    pk_field: str = "id"

    def __post_init__(self):
        # Find primary key
        for col in self.columns:
            if col.primary_key:
                self.pk_field = col.name
                break


class AdminRegistry:
    """Singleton registry for admin models."""

    _instance: AdminRegistry | None = None
    _models: dict[str, RegisteredModel] = {}

    def __new__(cls) -> AdminRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
        return cls._instance

    def register(self, model: type, admin_class: type[ModelAdmin] | None = None) -> RegisteredModel:
        """Register a model with the admin."""
        from fastapi_admin.views import ModelAdmin

        # Validate model is a SQLAlchemy mapped class
        if not hasattr(model, "__tablename__"):
            raise ValueError(f"{model.__name__} is not a SQLAlchemy model (no __tablename__)")

        # Create admin config
        if admin_class is None:
            admin = ModelAdmin()
        else:
            admin = admin_class()

        # Inspect the model
        columns, relationships = inspect_model(model)

        # Generate verbose names
        table_name = model.__tablename__
        verbose_name = admin.verbose_name or table_name.replace("_", " ").title()
        if admin.verbose_name_plural:
            verbose_name_plural = admin.verbose_name_plural
        elif verbose_name.endswith("y") and verbose_name[-2:].lower()[0] not in "aeiou":
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

        discovered = []
        seen_classes: set[type] = set()
        for subclass in _all_declarative_subclasses(DeclarativeBase):
            if hasattr(subclass, "registry"):
                for mapper in subclass.registry.mappers:
                    cls = mapper.class_
                    if cls not in seen_classes:
                        seen_classes.add(cls)
                        if hasattr(cls, "__tablename__") and cls.__tablename__ not in self._models:
                            registered = self.register(cls)
                            discovered.append(registered)
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
