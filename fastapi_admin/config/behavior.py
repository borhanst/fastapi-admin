"""Behavior configuration."""



class BehaviorConfig:
    """Behavior configuration."""

    def __init__(
        self,
        auto_discover: bool = True,
        dashboard_stats: list[str] | None = None,
        dashboard_charts: bool = True,
    ):
        self.auto_discover = auto_discover
        self.dashboard_stats = dashboard_stats or []
        self.dashboard_charts = dashboard_charts

    def validate_behavior_config(self) -> None:
        """Validate behavior configuration."""
        pass