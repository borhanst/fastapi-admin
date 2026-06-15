"""Admin template management and context building."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class AdminTemplate:
    """Manages Jinja2 template environment and sidebar context."""

    def __init__(
        self,
        title: str = "FastAPI Admin",
        logo_url: str | None = None,
        favicon_url: str | None = None,
        primary_color: str = "#0ea5e9",
        primary_color_dark: str = "#0284c7",
        dark_mode_default: bool = False,
    ):
        self.title = title
        self.logo_url = logo_url
        self.favicon_url = favicon_url
        self.primary_color = primary_color
        self.primary_color_dark = primary_color_dark
        self.dark_mode_default = dark_mode_default
        self._nav_groups_built: list = []

    def _init_jinja(self, app: Any) -> None:
        """Initialise the Jinja2 template environment."""
        import re
        from pathlib import Path

        from starlette.templating import Jinja2Templates

        templates_dir = Path(__file__).parent.parent / "templates"
        jinja_env = Jinja2Templates(directory=str(templates_dir))
        slugify = lambda s: (
            re.sub(r"[^\w]", "-", s, flags=re.A).strip("-").lower()
        )
        jinja_env.env.filters["slugify"] = slugify
        app.state.admin_jinja_env = jinja_env

    def sidebar_template_kwargs(self, request: Any) -> dict[str, Any]:
        """Thin wrapper — returns sidebar kwargs for TemplateResponse contexts."""
        return self.build_sidebar_context(request)

    def build_sidebar_context(self, request: Any, user: Any = None) -> dict:
        """Build per-request sidebar context (RBAC filter + permissions map)."""
        if user is None:
            user = getattr(request.state, "admin_user", None)

        from sqlalchemy.orm import Session

        from fastapi_admin.auth.permissions import PermissionChecker

        session: Session = request.app.state.admin_db_session
        checker = (
            PermissionChecker(session=session, user=user) if user else None
        )

        permissions_map: dict[str, Any] = {}
        nav_groups = self._nav_groups_built
        if checker:
            for group in nav_groups:
                for item in group.items:
                    table = item.permission_table
                    if table and table not in permissions_map:
                        permissions_map[table] = checker.permission_set(table)

        return {
            "nav_groups": nav_groups,
            "permissions_map": permissions_map,
            "current_user": user,
        }

    def apply_sidebar_context(
        self, request: Any, user: Any, context: dict
    ) -> dict:
        """Inject nav_groups + permissions_map into a template context dict."""
        context.update(self.build_sidebar_context(request, user=user))
        return context
