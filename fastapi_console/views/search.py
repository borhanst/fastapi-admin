"""Search endpoint factory for FK/M2M relation pickers."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy import select, or_, String
from fastapi_console.registry import RegisteredModel


def _get_searchable_columns(registered: RegisteredModel) -> list[str]:
    """Get columns to search across.
    
    If search_fields is configured, use those.
    Otherwise, fall back to the first String column.
    """
    if registered.admin.search_fields:
        return registered.admin.search_fields
    
    # Fallback to first String column
    string_cols = []
    for col in registered.columns:
        if isinstance(col.type, String):
            string_cols.append(col.name)
    return string_cols[:1]  # Return just the first String column


def search_factory(registered: RegisteredModel):
    async def search_view(
        request: Request,
        q: str = "",
        limit: int = 20,
        exclude_id: str | None = None,
        _: Any = None,
    ):
        session = request.app.state.admin_db_session
        model = registered.model
        base = select(model)
        
        # Build search clauses
        clauses = []
        if q:
            search_cols = _get_searchable_columns(registered)
            for col_name in search_cols:
                if hasattr(model, col_name):
                    col = getattr(model, col_name)
                    if hasattr(col, "ilike"):
                        clauses.append(col.ilike(f"%{q}%"))
        
        if clauses:
            base = base.where(or_(*clauses))
        
        # Handle self-referential FK exclusion
        if exclude_id is not None:
            pk_col = getattr(model, registered.pk_field)
            try:
                exclude_pk = type(pk_col.type)().process_result_value(
                    exclude_id, None
                ) if hasattr(pk_col.type, 'process_result_value') else exclude_id
            except (ValueError, TypeError):
                exclude_pk = exclude_id
            base = base.where(pk_col != exclude_pk)
        
        base = base.limit(limit)
        
        # Execute query - handle both sync and async sessions
        result = session.execute(base)
        if hasattr(result, '__await__'):
            result = await result
        rows = result.scalars().all()
        
        # Build results with proper label from admin.__str__
        results = []
        for row in rows:
            pk = getattr(row, registered.pk_field)
            label = registered.admin.__str__(row)
            results.append({"id": str(pk), "label": label})
        
        from fastapi.responses import JSONResponse
        return JSONResponse(results)
    
    search_view.__name__ = f"search_{registered.table_name}"
    return search_view
