"""Views package — re-exports ModelAdmin and route helpers."""

from fastapi_admin.modeladmin import ModelAdmin

__all__ = ["ModelAdmin", "create_model_router"]


def create_model_router(registered):  # type: ignore[no-untyped-def]
    """Build an APIRouter for a registered model.

    This is a stub — full route generation will be implemented in a later phase.
    """
    from fastapi import APIRouter

    router = APIRouter(prefix=f"/{registered.table_name}")

    @router.get("/")
    async def list_view():
        return {"model": registered.table_name, "action": "list"}

    return router
