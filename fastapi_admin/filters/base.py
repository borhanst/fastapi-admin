"""Filter ABCs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Filter(ABC):
    """Abstract base class for list view filters."""

    def __init__(self, field_name: str, label: str = "") -> None:
        self.field_name = field_name
        self.label = label or field_name.replace("_", " ").title()

    @abstractmethod
    def apply(self, query: Any, value: str) -> Any:
        """Apply the filter to a SQLAlchemy select query."""
        ...

    def get_choices(self, session: Any) -> list[tuple[str, str]]:
        """Return available filter choices as (value, label) pairs."""
        return []


class TextFilter(Filter):
    """Simple text equality filter."""

    def apply(self, query: Any, value: str) -> Any:
        model = query.column_descriptions[0]["entity"]
        if hasattr(model, self.field_name):
            col = getattr(model, self.field_name)
            return query.where(col == value)
        return query


class BooleanFilter(Filter):
    """Boolean filter — maps '1' to True, '0' to False."""

    def apply(self, query: Any, value: str) -> Any:
        model = query.column_descriptions[0]["entity"]
        if hasattr(model, self.field_name):
            col = getattr(model, self.field_name)
            return query.where(col == (value == "1"))
        return query


class RelationFilter(Filter):
    """Filter by foreign key relationship."""

    def apply(self, query: Any, value: str) -> Any:
        model = query.column_descriptions[0]["entity"]
        if hasattr(model, self.field_name):
            col = getattr(model, self.field_name)
            return query.where(col == value)
        return query


class EnumFilter(Filter):
    """Filter for enum columns."""

    def __init__(
        self,
        field_name: str,
        label: str = "",
        choices: list[str] | None = None,
    ) -> None:
        super().__init__(field_name, label)
        self._enum_choices = choices or []

    def apply(self, query: Any, value: str) -> Any:
        model = query.column_descriptions[0]["entity"]
        if hasattr(model, self.field_name):
            col = getattr(model, self.field_name)
            return query.where(col == value)
        return query

    def get_choices(self, session: Any) -> list[tuple[str, str]]:
        choices = [("", "All")]
        for val in self._enum_choices:
            choices.append((val, val.replace("_", " ").title()))
        return choices
