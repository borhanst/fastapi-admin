"""Dashboard view handler factory."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from fastapi_console.auth.dependencies import get_current_admin_user


def _get_sync_engine(request: Request):
    """Get or create a sync engine from the async engine in app.state."""
    from sqlalchemy.ext.asyncio import AsyncEngine

    async_engine = request.app.state.admin_engine
    if not isinstance(async_engine, AsyncEngine):
        return async_engine

    if not hasattr(request.app.state, "_admin_sync_engine"):
        sync_url = str(async_engine.url)
        for suffix in ("+aiosqlite", "+asyncpg", "+asyncmy"):
            sync_url = sync_url.replace(suffix, "")
        request.app.state._admin_sync_engine = create_engine(sync_url, echo=False)
    return request.app.state._admin_sync_engine


def dashboard_view_factory(admin: Any):
    """Return a dashboard view function bound to the given admin instance."""
    async def dashboard_view(
        request: Request,
        current_user: Any = Depends(get_current_admin_user),
    ):
        templates = request.app.state.admin_jinja_env
        admin_instance = request.app.state.admin
        config = request.app.state.admin_config

        # Get registered models
        registered_models = admin_instance.registry.all()

        # Determine which models to show stats for
        dashboard_stats = config.get("dashboard_stats", [])
        if dashboard_stats:
            models_for_stats = [
                m for m in registered_models if m.table_name in dashboard_stats
            ]
        else:
            models_for_stats = registered_models

        # Get record counts for each model using a session
        stat_cards = []
        engine = _get_sync_engine(request)
        session = Session(engine)
        try:
            for model in models_for_stats:
                count_query = select(func.count()).select_from(model.model)
                count = session.execute(count_query).scalar()
                stat_cards.append({
                    "title": model.verbose_name_plural,
                    "count": count,
                    "url": f"{admin_instance.admin_path}/{model.table_name}/",
                })

            # Fetch last 10 audit entries
            from fastapi_console.audit.models import AuditLog
            audit_query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10)
            recent_audit = session.execute(audit_query).scalars().all()
        finally:
            session.close()

        # Check if charts are enabled
        show_charts = config.get("dashboard_charts", True)

        template = templates.get_template("pages/dashboard.html")
        context: dict[str, Any] = {
            "request": request,
            "registered_models": registered_models,
            "stat_cards": stat_cards,
            "recent_audit": recent_audit,
            "show_charts": show_charts,
            "admin_path": admin_instance.admin_path,
            "title": admin_instance.title,
        }
        if hasattr(admin_instance, "build_sidebar_context") and current_user is not None:
            context.update(admin_instance.build_sidebar_context(request, user=current_user))
        html = template.render(**context)
        return HTMLResponse(content=html)

    dashboard_view.__name__ = "dashboard"
    return dashboard_view
