"""RBAC permission checker — per-request, with in-memory caching."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_admin.auth.models import AdminFieldPermission, AdminPermission
from fastapi_admin.types import PermissionSet

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from fastapi_admin.auth.protocol import AdminUserProtocol


class PermissionChecker:
    """Per-request permission checker.

    Instantiated once per request via ``Depends(get_permission_checker)``.
    Caches permission results in-memory for the lifetime of the request.
    """

    def __init__(self, session: Session, user: AdminUserProtocol) -> None:
        self.session = session
        self.user = user
        self._cache: dict[tuple[str, str], bool] = {}
        self._field_cache: dict[tuple[str, str], set[str] | None] = {}

    def has_permission(self, table_name: str, action: str) -> bool:
        """Return True if the current user may perform *action* on *table_name*.

        Actions: ``"view"`` | ``"create"`` | ``"edit"`` | ``"delete"``

        Superusers always return True.  Results are cached per-request.
        """
        if self.user.is_superuser:
            return True

        cache_key = (table_name, action)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.user.role_id is None:
            self._cache[cache_key] = False
            return False

        perm = (
            self.session.query(AdminPermission)
            .filter_by(role_id=self.user.role_id, table_name=table_name)
            .first()
        )

        result = bool(perm and getattr(perm, f"can_{action}", False))
        self._cache[cache_key] = result
        return result

    def get_allowed_fields(self, table_name: str, mode: str) -> set[str] | None:
        """Return the set of field names the user may access, or ``None``.

        mode: ``"view"`` | ``"edit"``

        Semantics:
        - ``None`` → no field-level restrictions exist → all fields allowed.
        - Empty ``set()`` → restriction rows exist but none grant access → no fields.
        - Non-empty ``set()`` → only those field names are permitted.
        """
        if self.user.is_superuser:
            return None

        cache_key = (table_name, mode)
        if cache_key in self._field_cache:
            return self._field_cache[cache_key]

        if self.user.role_id is None:
            self._field_cache[cache_key] = set()
            return set()

        rows = (
            self.session.query(AdminFieldPermission)
            .filter_by(role_id=self.user.role_id, table_name=table_name)
            .all()
        )

        if not rows:
            self._field_cache[cache_key] = None
            return None

        attr = "can_view" if mode == "view" else "can_edit"
        allowed = {r.field_name for r in rows if getattr(r, attr)}
        self._field_cache[cache_key] = allowed
        return allowed

    def permission_set(self, table_name: str) -> PermissionSet:
        """Return a :class:`PermissionSet` for convenient template / UI use."""
        return PermissionSet(
            can_view=self.has_permission(table_name, "view"),
            can_create=self.has_permission(table_name, "create"),
            can_edit=self.has_permission(table_name, "edit"),
            can_delete=self.has_permission(table_name, "delete"),
        )
