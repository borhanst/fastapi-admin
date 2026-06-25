"""Dashboard view handler factory."""

from __future__ import annotations

import importlib
from typing import Any

from fastapi import Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func

from fastapi_admin.auth.dependencies import get_current_admin_user


def _resolve_callback(dotted_path: str) -> Any | None:
    """Resolve a dotted path like 'myapp.dashboards.custom_stats' to the function."""
    if not dotted_path:
        return None
    try:
        module_path, _, func_name = dotted_path.rpartition(".")
        module = importlib.import_module(module_path)
        return getattr(module, func_name, None)
    except (ImportError, AttributeError):
        return None


def dashboard_view_factory(admin: Any):
    """Return a dashboard view function bound to the given admin instance."""
    async def dashboard_view(
        request: Request,
        current_user: Any = Depends(get_current_admin_user),
    ):
        templates = request.app.state.admin_jinja_env
        admin_instance = request.app.state.admin
        config = request.app.state.admin_config
        session = request.app.state.admin_db_session

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

        # Get record counts for each model
        stat_cards = []
        for model in models_for_stats:
            count_query = select(func.count()).select_from(model.model)
            count = (await session.execute(count_query)).scalar()
            stat_cards.append({
                "title": model.verbose_name_plural,
                "count": count,
                "url": f"{admin_instance.admin_path}/{model.table_name}/",
            })

        # Fetch last 10 audit entries
        from fastapi_admin.audit.models import AuditLog
        audit_query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10)
        recent_audit = (await session.execute(audit_query)).scalars().all()

        # Check if charts are enabled
        show_charts = config.get("dashboard_charts", True)

        # Resolve dashboard callback if configured
        dashboard_callback = admin_instance.config.behavior.dashboard_callback
        callback_data = {}
        if dashboard_callback:
            cb_fn = _resolve_callback(dashboard_callback)
            if cb_fn and callable(cb_fn):
                import asyncio
                if asyncio.iscoroutinefunction(cb_fn):
                    callback_data = await cb_fn(request, session) or {}
                else:
                    callback_data = cb_fn(request, session) or {}

        # Dashboard components
        dashboard_components = admin_instance.config.behavior.dashboard_components

        template = templates.get_template("pages/dashboard.html")
        context: dict[str, Any] = {
            "request": request,
            "registered_models": registered_models,
            "stat_cards": stat_cards,
            "recent_audit": recent_audit,
            "show_charts": show_charts,
            "admin_path": admin_instance.admin_path,
            "title": admin_instance.title,
            "dashboard_callback_data": callback_data,
            "dashboard_components": dashboard_components,
        }
        if hasattr(admin_instance, "build_sidebar_context") and current_user is not None:
            context.update(admin_instance.build_sidebar_context(request, user=current_user))
        html = template.render(**context)
        return HTMLResponse(content=html)

    dashboard_view.__name__ = "dashboard"
    return dashboard_view
