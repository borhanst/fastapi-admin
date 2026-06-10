"""Tests for Phase 10 — Auth Routes (Login / Logout)."""

from __future__ import annotations

import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fastapi_admin import Admin
from fastapi_admin.auth.backend import BuiltinAuthBackend
from fastapi_admin.auth.models import AdminRole, AdminUser
from fastapi_admin.models import Base


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


import tempfile
import os

@pytest.fixture
def engine():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    yield engine
    os.unlink(path)


@pytest.fixture
def admin_user(engine):
    """Create a test admin user."""
    with Session(engine) as session:
        # Create a role
        role = AdminRole(name="SuperAdmin", description="Super admin")
        session.add(role)
        session.flush()

        # Create a user
        user = AdminUser(
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
            full_name="Test User",
            role_id=role.id,
            is_superuser=True,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print("Created admin user with id:", user.id)
        return user


@pytest.fixture
def client(engine, admin_user):
    """Create a TestClient for the admin app."""
    admin = Admin(
        engine=engine,
        auth_model=AdminUser,
        auth_backend=BuiltinAuthBackend(),
        secret_key="test-secret-key",
    )
    app = FastAPI()
    # Run the async setup
    asyncio.run(admin.setup(app))
    # Debug: print tables and count of admin_users after setup
    from sqlalchemy import inspect
    inspector = inspect(engine)
    print("Tables in engine after setup:", inspector.get_table_names())
    with Session(engine) as session:
        count = session.query(AdminUser).count()
        print("Number of admin_users after setup:", count)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_login_get_redirects_when_authenticated(client):
    """GET /admin/login redirects if already authenticated."""
    # First, log in via POST to get a session
    response = client.post(
        "/admin/login",
        data={"email": "test@example.com", "password": "secret"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    # Extract the session cookie
    cookie = response.headers["set-cookie"]
    # Now, GET /admin/login with that cookie should redirect to /admin/
    response = client.get(
        "/admin/login",
        headers={"Cookie": cookie},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/"


def test_login_get_shows_form_when_not_authenticated(client):
    """GET /admin/login shows the login form when not authenticated."""
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "Admin Login" in response.text
    assert '<form method="post">' in response.text


def test_login_post_successful(client):
    """POST /admin/login with valid credentials sets session cookie."""
    response = client.post(
        "/admin/login",
        data={"email": "test@example.com", "password": "secret"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    # Should redirect to /admin/ (since no next param)
    assert response.headers["location"] == "/admin/"
    # Should have set a session cookie
    assert "admin_session=" in response.headers["set-cookie"]


def test_login_post_failed(client):
    """POST /admin/login with invalid credentials re-renders with error."""
    response = client.post(
        "/admin/login",
        data={"email": "test@example.com", "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Invalid email or password" in response.text


def test_login_post_next_redirect(client):
    """POST /admin/login respects safe next URL."""
    response = client.post(
        "/admin/login",
        data={"email": "test@example.com", "password": "secret", "next": "/admin/some/model/"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/some/model/"


def test_login_post_next_open_redirect_blocked(client):
    """POST /admin/login blocks open redirect via next param."""
    response = client.post(
        "/admin/login",
        data={"email": "test@example.com", "password": "secret", "next": "http://evil.com"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    # Should fall back to /admin/
    assert response.headers["location"] == "/admin/"


def test_logout_post_clears_cookie(client):
    """POST /admin/logout clears the session cookie."""
    # First, log in
    response = client.post(
        "/admin/login",
        data={"email": "test@example.com", "password": "secret"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    cookie = response.headers["set-cookie"]

    # Now, log out
    response = client.post(
        "/admin/logout",
        headers={"Cookie": cookie},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"
    # The cookie should be expired (deleted)
    set_cookie = response.headers["set-cookie"]
    assert "Max-Age=0" in set_cookie or "Expires=" in set_cookie


def test_logout_post_when_not_logged_in(client):
    """POST /admin/logout when not logged in redirects to login."""
    response = client.post("/admin/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"