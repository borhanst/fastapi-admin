"""Navigation configuration."""

from typing import Any

from fastapi_admin.exceptions import ConfigError


class NavConfig:
    """Navigation configuration."""

    def __init__(
        self,
        nav_groups: list[Any] | None = None,
        sidebar_builder: Any | None = None,
        require_tags: bool = False,
    ):
        self.nav_groups = nav_groups or []
        self.sidebar_builder = sidebar_builder
        self.require_tags = require_tags

    def validate_nav_config(self) -> None:
        """Validate navigation configuration."""
        if self.require_tags and not self.nav_groups:
            raise ConfigError("require_tags=True requires nav_groups to be configured")