"""RBAC permission checker — per-request, with in-memory caching."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_console.auth.models import AdminFieldPermission, AdminPermission
from fastapi_console.types import PermissionSet

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from fastapi_console.auth.protocol import AdminUserProtocol


class PermissionChecker:
    """Per-request permission checker.

    Instantiated once per request via ``Depends(get_permission_checker)``.
    Caches permission results in-memory for the lifetime of the request.
    """

    def __init__(
        self,
        session: AsyncSession,
        user: AdminUserProtocol,
        *,
        user_snapshot: dict[str, object] | None = None,
    ) -> None:
        self.session = session
        self.user = user
        snap = user_snapshot or {}
        self._is_superuser: bool = (
            bool(snap["is_superuser"]) if "is_superuser" in snap else bool(user.is_superuser)
        )
        self._role_id: int | None = (
            snap["role_id"] if "role_id" in snap else user.role_id
        )
        self._cache: dict[tuple[str, str], bool] = {}
        self._field_cache: dict[tuple[str, str], set[str] | None] = {}

    async def has_permission(self, table_name: str, action: str) -> bool:
        """Return True if the current user may perform *action* on *table_name*.

        Actions: ``"view"`` | ``"create"`` | ``"edit"`` | ``"delete"``

        Superusers always return True.  Results are cached per-request.
        """
        if self._is_superuser:
            return True

        cache_key = (table_name, action)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self._role_id is None:
            self._cache[cache_key] = False
            return False

        from sqlalchemy import select

        result = await self.session.execute(
            select(AdminPermission).where(
                AdminPermission.role_id == self._role_id,
                AdminPermission.table_name == table_name,
            )
        )
        perm = result.scalar_one_or_none()

        result_bool = bool(perm and getattr(perm, f"can_{action}", False))
        self._cache[cache_key] = result_bool
        return result_bool

    async def get_allowed_fields(self, table_name: str, mode: str) -> set[str] | None:
        """Return the set of field names the user may access, or ``None``.

        mode: ``"view"`` | ``"edit"``

        Semantics:
        - ``None`` → no field-level restrictions exist → all fields allowed.
        - Empty ``set()`` → restriction rows exist but none grant access → no fields.
        - Non-empty ``set()`` → only those field names are permitted.
        """
        if self._is_superuser:
            return None

        cache_key = (table_name, mode)
        if cache_key in self._field_cache:
            return self._field_cache[cache_key]

        if self._role_id is None:
            self._field_cache[cache_key] = set()
            return set()

        from sqlalchemy import select

        result = await self.session.execute(
            select(AdminFieldPermission).where(
                AdminFieldPermission.role_id == self._role_id,
                AdminFieldPermission.table_name == table_name,
            )
        )
        rows = result.scalars().all()

        if not rows:
            self._field_cache[cache_key] = None
            return None

        attr = "can_view" if mode == "view" else "can_edit"
        allowed = {r.field_name for r in rows if getattr(r, attr)}
        self._field_cache[cache_key] = allowed
        return allowed

    def permission_set(self, table_name: str) -> PermissionSet:
        """Return a :class:`PermissionSet` for convenient template / UI use.

        Note: This is a sync convenience wrapper. For async contexts,
        use the individual async methods directly.
        """
        if self._is_superuser:
            return PermissionSet(
                can_view=True,
                can_create=True,
                can_edit=True,
                can_delete=True,
            )
        return PermissionSet(
            can_view=self._cache.get((table_name, "view"), False),
            can_create=self._cache.get((table_name, "create"), False),
            can_edit=self._cache.get((table_name, "edit"), False),
            can_delete=self._cache.get((table_name, "delete"), False),
        )

    async def load_permissions(self, table_name: str) -> PermissionSet:
        """Async method to load and cache all permissions for a table.

        Call this before using ``permission_set()`` to ensure the cache is populated.
        """
        await self.has_permission(table_name, "view")
        await self.has_permission(table_name, "create")
        await self.has_permission(table_name, "edit")
        await self.has_permission(table_name, "delete")
        return self.permission_set(table_name)
