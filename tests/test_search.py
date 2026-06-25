"""Tests for Phase 18 — Relation Search Endpoint."""

from __future__ import annotations

import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship

from fastapi_console.models.base import Base as AdminBase
from fastapi_console.registry import AdminRegistry


# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class _Base(DeclarativeBase):
    pass


class _Category(_Base):
    __tablename__ = "search_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)


class _Product(_Base):
    __tablename__ = "search_products"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    category_id = Column(Integer, ForeignKey("search_categories.id"))

    category = relationship("_Category")


class _SelfRef(_Base):
    """Self-referential FK model for testing exclude_id."""
    __tablename__ = "search_selfref"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("search_selfref.id"))

    parent = relationship("_SelfRef", remote_side="[_SelfRef.id]")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_registry():
    AdminRegistry().clear()
    yield
    AdminRegistry().clear()


@pytest.fixture()
def engine():
    # Set env to allow table creation
    os.environ["SKIP_CREATE_TABLES"] = "false"
    engine = create_engine("sqlite:///:memory:")
    AdminBase.metadata.create_all(bind=engine)
    _Base.metadata.create_all(bind=engine)
    yield engine
    os.environ.pop("SKIP_CREATE_TABLES", None)


@pytest.fixture()
def app():
    return FastAPI()


@pytest.fixture()
async def admin_app(app, engine):
    from fastapi_console.admin import Admin

    admin = Admin(app=app, engine=engine, secret_key="test-secret-key-long-enough-for-security!", auto_discover=False)
    admin.register(_Category)
    admin.register(_Product)
    admin.register(_SelfRef)
    await admin.setup()
    return app


@pytest.fixture()
def seed_data(engine):
    with Session(engine) as session:
        cat1 = _Category(name="Electronics")
        cat2 = _Category(name="Books")
        session.add_all([cat1, cat2])
        session.flush()

        p1 = _Product(name="Laptop", description="Gaming laptop", category_id=cat1.id)
        p2 = _Product(name="Phone", description="Smart phone", category_id=cat1.id)
        p3 = _Product(name="Novel", description="Fiction book", category_id=cat2.id)
        session.add_all([p1, p2, p3])
        session.flush()

        # Self-referential data
        parent = _SelfRef(name="Parent")
        session.add(parent)
        session.flush()
        child = _SelfRef(name="Child", parent_id=parent.id)
        session.add(child)
        session.commit()


# ---------------------------------------------------------------------------
# 18.7 — Tests
# ---------------------------------------------------------------------------


class TestSearchReturnsResults:
    def test_search_returns_matching_results(self, admin_app, seed_data):
        client = TestClient(admin_app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "Laptop"},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["label"] == "Laptop"

    def test_search_is_case_insensitive(self, admin_app, seed_data):
        client = TestClient(admin_app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "laptop"},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_search_multiple_matches(self, admin_app, seed_data):
        client = TestClient(admin_app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "phone"},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1  # "Phone" matches

    def test_empty_query_returns_first_records(self, admin_app, seed_data):
        client = TestClient(admin_app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "", "limit": 2},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_limit_controls_result_count(self, admin_app, seed_data):
        client = TestClient(admin_app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "", "limit": 1},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1


class TestSearchExcludeId:
    def test_exclude_id_removes_record(self, admin_app, seed_data):
        client = TestClient(admin_app)
        # First get all products
        resp_all = client.get(
            "/admin/search_products/search",
            params={"q": ""},
            cookies={"admin_session": "dummy"},
        )
        all_products = resp_all.json()
        assert len(all_products) == 3

        # Exclude the first product
        exclude_id = all_products[0]["id"]
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "", "exclude_id": exclude_id},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(item["id"] != exclude_id for item in data)

    def test_exclude_id_self_referential(self, admin_app, seed_data):
        client = TestClient(admin_app)
        # Get all self-ref records
        resp_all = client.get(
            "/admin/search_selfref/search",
            params={"q": ""},
            cookies={"admin_session": "dummy"},
        )
        all_records = resp_all.json()
        assert len(all_records) == 2

        # Exclude the parent so child can't select itself as parent
        parent_id = next(r["id"] for r in all_records if r["label"] == "Parent")
        resp = client.get(
            "/admin/search_selfref/search",
            params={"q": "", "exclude_id": parent_id},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["label"] == "Child"


class TestSearchFallback:
    def test_fallback_to_string_column(self, engine):
        """When search_fields is None, search should fall back to first String column."""
        AdminRegistry().clear()
        app = FastAPI()

        admin = Admin(app=app, engine=engine, secret_key="test-secret-key-long-enough-for-security!", auto_discover=False)
        # Register without search_fields — should fallback to 'name' column
        admin.register(_Product)

        # We need to run setup to wire the app state
        import asyncio
        asyncio.get_event_loop().run_until_complete(admin.setup())

        client = TestClient(app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "Laptop"},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["label"] == "Laptop"


class TestSearchUnauthorized:
    def test_unauthorized_returns_401(self, admin_app, seed_data):
        client = TestClient(admin_app)
        # No cookies — should return 401 or 403
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "Laptop"},
        )
        assert resp.status_code in {401, 403}


class TestSearchLabel:
    def test_label_uses_admin_str(self, admin_app, seed_data):
        """Verify that the label is generated by admin.__str__(obj)."""
        client = TestClient(admin_app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": ""},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Default ModelAdmin.__str__ returns name attribute if present
        labels = {item["label"] for item in data}
        assert "Laptop" in labels
        assert "Phone" in labels
        assert "Novel" in labels


class TestSearchJSON:
    def test_returns_json_format(self, admin_app, seed_data):
        client = TestClient(admin_app)
        resp = client.get(
            "/admin/search_products/search",
            params={"q": "Laptop"},
            cookies={"admin_session": "dummy"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "label" in data[0]
