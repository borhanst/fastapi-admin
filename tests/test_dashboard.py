"""Tests for the dashboard view."""

import os
import tempfile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fastapi_console import Admin
from fastapi_console.auth.backend import BuiltinAuthBackend
from fastapi_console.auth.models import AdminRole, AdminUser
from fastapi_console.audit.models import AuditLog  # noqa: F401 - ensure table is registered
from fastapi_console.models.base import Base as AdminBase
from tests.test_registry import Product, Category


@pytest.fixture
def engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    AdminBase.metadata.create_all(engine)
    Product.metadata.create_all(engine)
    yield engine
    os.unlink(path)


@pytest.fixture
def admin_user(engine):
    with Session(engine) as session:
        role = AdminRole(name="SuperAdmin")
        session.add(role)
        session.flush()
        user = AdminUser(
            email="admin@test.com",
            hashed_password="$2b$12$slFfzZIMUc6WocnpyNUlKeHm/ihzmppP9yEYtR2aUBBKuZ8ojGcAy",
            full_name="Admin",
            is_superuser=True,
            is_active=True,
        )
        user.roles.append(role)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def client(engine, admin_user):
    app = FastAPI()
    admin = Admin(
        app=app,
        engine=engine,
        secret_key="test-secret-key-long-enough-for-security!",
        auth_backend=BuiltinAuthBackend(),
        auto_discover=False,
    )
    # Run setup synchronously (admin.setup() is async but we use asyncio.run)
    import asyncio
    asyncio.run(admin.setup(app))

    # Register Product model
    admin.register(Product)

    # Add test data
    SessionLocal = sessionmaker(engine)
    db = SessionLocal()
    try:
        cat = Category(name="Test Category")
        db.add(cat)
        db.flush()
        for i in range(3):
            product = Product(
                name=f"Product {i}",
                price=100 + i,
                category_id=cat.id,
                is_active=True,
            )
            db.add(product)
        db.commit()
    finally:
        db.close()

    return TestClient(app), admin, engine


def test_dashboard_view(client):
    """Test the dashboard view shows correct stat counts and recent activity."""
    test_client, admin, engine = client

    # Login first
    response = test_client.post(
        "/admin/login",
        data={"email": "admin@test.com", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    session_cookie = response.cookies.get("admin_session")

    # Access dashboard
    cookies = {"admin_session": session_cookie} if session_cookie else {}
    response = test_client.get("/admin/", cookies=cookies)
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Products" in response.text
    assert "3" in response.text  # 3 products

    # Check recent activity section exists
    assert "Recent Activity" in response.text

    # Check quick create link
    assert "Add Product" in response.text
    assert "/admin/products/create" in response.text


def test_dashboard_stats_filter(client):
    """Test that dashboard_stats config filters which models are shown."""
    test_client, admin, engine = client

    # Login
    response = test_client.post(
        "/admin/login",
        data={"email": "admin@test.com", "password": "password"},
        follow_redirects=False,
    )
    session_cookie = response.cookies.get("admin_session")
    cookies = {"admin_session": session_cookie} if session_cookie else {}

    # Set dashboard_stats to include only products
    admin.dashboard_stats = ["products"]
    test_client.app.state.admin_config["dashboard_stats"] = ["products"]

    response = test_client.get("/admin/", cookies=cookies)
    assert response.status_code == 200
    assert "3" in response.text  # Should still show products count


def test_dashboard_charts_toggle(client):
    """Test that dashboard_charts config controls chart visibility."""
    test_client, admin, engine = client

    # Login
    response = test_client.post(
        "/admin/login",
        data={"email": "admin@test.com", "password": "password"},
        follow_redirects=False,
    )
    session_cookie = response.cookies.get("admin_session")
    cookies = {"admin_session": session_cookie} if session_cookie else {}

    # Charts shown by default
    response = test_client.get("/admin/", cookies=cookies)
    assert response.status_code == 200
    assert "Charts" in response.text

    # Disable charts
    admin.dashboard_charts = False
    test_client.app.state.admin_config["dashboard_charts"] = False

    response = test_client.get("/admin/", cookies=cookies)
    assert response.status_code == 200
    assert "Charts" not in response.text
