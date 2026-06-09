"""Auto-route generation per registered model."""

from __future__ import annotations

from fastapi import FastAPI

from fastapi_admin.registry import AdminRegistry
from fastapi_admin.views import create_model_router


def register_admin_routes(app: FastAPI, prefix: str = "/admin") -> None:
    """Register all admin routes with the FastAPI app."""
    registry = AdminRegistry()

    # Auto-discover any unregistered models
    registry.auto_discover()

    # Create routes for each registered model
    for registered in registry.all():
        model_router = create_model_router(registered)
        app.include_router(model_router, prefix=prefix)

    # Dashboard route
    @app.get(prefix, tags=["admin"])
    async def admin_dashboard():
        from fastapi.responses import HTMLResponse

        models_html = "".join(
            f'<li><a href="{prefix}/{m.table_name}/">{m.verbose_name_plural}</a></li>'
            for m in registry.all()
        )
        return HTMLResponse(
            f"<h1>Admin Dashboard</h1><ul>{models_html or '<li>No models registered</li>'}</ul>"
        )
