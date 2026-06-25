"""Tests for Phase 8 — RBAC Permission Checker."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fastapi_console.auth.models import (
    AdminFieldPermission,
    AdminPermission,
    AdminRole,
    AdminUser,
)
from fastapi_console.auth.permissions import PermissionChecker
from fastapi_console.models import Base
from fastapi_console.types import PermissionSet


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def editor_role(session):
    role = AdminRole(name="Editor")
    session.add(role)
    session.flush()
    return role


@pytest.fixture
def viewer_role(session):
    role = AdminRole(name="Viewer")
    session.add(role)
    session.flush()
    return role


@pytest.fixture
def superuser(session, editor_role):
    user = AdminUser(
        email="super@example.com",
        hashed_password="hash",
        full_name="Super Admin",
        role_id=editor_role.id,
        is_superuser=True,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


@pytest.fixture
def normal_user(session, editor_role):
    user = AdminUser(
        email="editor@example.com",
        hashed_password="hash",
        full_name="Editor",
        role_id=editor_role.id,
        is_superuser=False,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


@pytest.fixture
def no_role_user(session):
    user = AdminUser(
        email="norole@example.com",
        hashed_password="hash",
        full_name="No Role",
        role_id=None,
        is_superuser=False,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


# ---------------------------------------------------------------------------
# 8.1 / 8.2 — has_permission: superuser bypass
# ---------------------------------------------------------------------------


class TestHasPermissionSuperuser:
    def test_superuser_always_allowed(self, session, superuser):
        checker = PermissionChecker(session=session, user=superuser)
        for action in ("view", "create", "edit", "delete"):
            assert checker.has_permission("any_table", action) is True

    def test_superuser_allowed_even_without_permissions(self, session, superuser):
        checker = PermissionChecker(session=session, user=superuser)
        assert checker.has_permission("nonexistent_table", "view") is True


# ---------------------------------------------------------------------------
# 8.2 — has_permission: no role
# ---------------------------------------------------------------------------


class TestHasPermissionNoRole:
    def test_no_role_always_denied(self, session, no_role_user):
        checker = PermissionChecker(session=session, user=no_role_user)
        for action in ("view", "create", "edit", "delete"):
            assert checker.has_permission("any_table", action) is False


# ---------------------------------------------------------------------------
# 8.2 — has_permission: normal user with permissions
# ---------------------------------------------------------------------------


class TestHasPermissionNormalUser:
    def test_with_permission_granted(self, session, editor_role, normal_user):
        perm = AdminPermission(
            role_id=editor_role.id,
            table_name="products",
            can_view=True,
            can_create=True,
            can_edit=False,
            can_delete=False,
        )
        session.add(perm)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        assert checker.has_permission("products", "view") is True
        assert checker.has_permission("products", "create") is True
        assert checker.has_permission("products", "edit") is False
        assert checker.has_permission("products", "delete") is False

    def test_without_permission_row_denied(self, session, normal_user):
        checker = PermissionChecker(session=session, user=normal_user)
        assert checker.has_permission("products", "view") is False

    def test_wrong_table_denied(self, session, editor_role, normal_user):
        perm = AdminPermission(
            role_id=editor_role.id,
            table_name="products",
            can_view=True,
        )
        session.add(perm)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        assert checker.has_permission("orders", "view") is False

    def test_custom_action_name(self, session, editor_role, normal_user):
        perm = AdminPermission(
            role_id=editor_role.id,
            table_name="orders",
            can_view=True,
        )
        session.add(perm)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        assert checker.has_permission("orders", "view") is True
        assert checker.has_permission("orders", "ship") is False


# ---------------------------------------------------------------------------
# 8.2 — has_permission: caching
# ---------------------------------------------------------------------------


class TestHasPermissionCaching:
    def test_result_is_cached(self, session, editor_role, normal_user):
        perm = AdminPermission(
            role_id=editor_role.id,
            table_name="products",
            can_view=True,
        )
        session.add(perm)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)

        first = checker.has_permission("products", "view")
        second = checker.has_permission("products", "view")
        assert first is True
        assert second is True
        assert ("products", "view") in checker._cache

    def test_different_actions_not_shared(self, session, editor_role, normal_user):
        perm = AdminPermission(
            role_id=editor_role.id,
            table_name="products",
            can_view=True,
            can_delete=False,
        )
        session.add(perm)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        assert checker.has_permission("products", "view") is True
        assert checker.has_permission("products", "delete") is False


# ---------------------------------------------------------------------------
# 8.3 — get_allowed_fields
# ---------------------------------------------------------------------------


class TestGetAllowedFields:
    def test_superuser_returns_none(self, session, superuser):
        checker = PermissionChecker(session=session, user=superuser)
        assert checker.get_allowed_fields("products", "view") is None

    def test_no_role_returns_empty_set(self, session, no_role_user):
        checker = PermissionChecker(session=session, user=no_role_user)
        assert checker.get_allowed_fields("products", "view") == set()

    def test_no_field_rows_returns_none(self, session, editor_role, normal_user):
        checker = PermissionChecker(session=session, user=normal_user)
        assert checker.get_allowed_fields("products", "view") is None

    def test_returns_allowed_view_fields(self, session, editor_role, normal_user):
        fields = [
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="name",
                can_view=True,
                can_edit=True,
            ),
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="price",
                can_view=True,
                can_edit=False,
            ),
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="secret",
                can_view=False,
                can_edit=False,
            ),
        ]
        session.add_all(fields)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        allowed = checker.get_allowed_fields("products", "view")
        assert allowed == {"name", "price"}

    def test_returns_allowed_edit_fields(self, session, editor_role, normal_user):
        fields = [
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="name",
                can_view=True,
                can_edit=True,
            ),
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="price",
                can_view=True,
                can_edit=False,
            ),
        ]
        session.add_all(fields)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        allowed = checker.get_allowed_fields("products", "edit")
        assert allowed == {"name"}

    def test_all_fields_denied_returns_empty_set(self, session, editor_role, normal_user):
        fields = [
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="name",
                can_view=False,
                can_edit=False,
            ),
        ]
        session.add_all(fields)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        allowed = checker.get_allowed_fields("products", "view")
        assert allowed == set()

    def test_wrong_table_returns_none(self, session, editor_role, normal_user):
        fields = [
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="name",
                can_view=True,
                can_edit=True,
            ),
        ]
        session.add_all(fields)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        assert checker.get_allowed_fields("orders", "view") is None

    def test_field_cache(self, session, editor_role, normal_user):
        fields = [
            AdminFieldPermission(
                role_id=editor_role.id,
                table_name="products",
                field_name="name",
                can_view=True,
                can_edit=True,
            ),
        ]
        session.add_all(fields)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        first = checker.get_allowed_fields("products", "view")
        second = checker.get_allowed_fields("products", "view")
        assert first == {"name"}
        assert first is second


# ---------------------------------------------------------------------------
# 8.4 — permission_set
# ---------------------------------------------------------------------------


class TestPermissionSet:
    def test_returns_permission_set(self, session, editor_role, normal_user):
        perm = AdminPermission(
            role_id=editor_role.id,
            table_name="products",
            can_view=True,
            can_create=True,
            can_edit=False,
            can_delete=False,
        )
        session.add(perm)
        session.flush()

        checker = PermissionChecker(session=session, user=normal_user)
        ps = checker.permission_set("products")
        assert isinstance(ps, PermissionSet)
        assert ps.can_view is True
        assert ps.can_create is True
        assert ps.can_edit is False
        assert ps.can_delete is False

    def test_no_permission_returns_all_false(self, session, normal_user):
        checker = PermissionChecker(session=session, user=normal_user)
        ps = checker.permission_set("products")
        assert ps.can_view is False
        assert ps.can_create is False
        assert ps.can_edit is False
        assert ps.can_delete is False

    def test_superuser_returns_all_true(self, session, superuser):
        checker = PermissionChecker(session=session, user=superuser)
        ps = checker.permission_set("products")
        assert ps.can_view is True
        assert ps.can_create is True
        assert ps.can_edit is True
        assert ps.can_delete is True
