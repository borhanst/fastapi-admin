"""Action ABCs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fastapi import Request


class Action(ABC):
    """Abstract base class for bulk list-view actions."""

    def __init__(
        self, name: str, label: str = "", confirmation_message: str = ""
    ) -> None:
        self.name = name
        self.label = label or name.replace("_", " ").title()
        self.confirmation_message = confirmation_message

    @abstractmethod
    async def execute(
        self, objects: list[Any], request: Request | None
    ) -> None:
        """Run the action against the selected objects."""
        ...

    def get_confirmation_message(self) -> str:
        return self.confirmation_message or f"Run {self.label}?"
