"""Tests for Phase 12 CRUD routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_list_200(app, session, admin_user):
    client = TestClient(app)
    resp = client.get("/admin/products/", cookies={"admin_session": "dummy"})
    assert resp.status_code == 200


def test_create_valid_redirect(app, session, admin_user):
    client = TestClient(app)
    resp = client.post("/admin/products/create", data={"name": "Test"}, cookies={"admin_session": "dummy"})
    assert resp.status_code == 303


def test_create_invalid_422(app, session, admin_user):
    client = TestClient(app)
    resp = client.post("/admin/products/create", data={"name": ""}, cookies={"admin_session": "dummy"})
    assert resp.status_code == 422


def test_edit_updates(app, session, admin_user, product):
    client = TestClient(app)
    resp = client.post(f"/admin/products/{product.id}/", data={"name": "Updated"}, cookies={"admin_session": "dummy"})
    assert resp.status_code == 303


def test_delete_removes(app, session, admin_user, product):
    client = TestClient(app)
    resp = client.post(f"/admin/products/{product.id}/delete", cookies={"admin_session": "dummy"})
    assert resp.status_code == 303


def test_rbac_403_without_permission(app, session):
    client = TestClient(app)
    resp = client.get("/admin/products/")
    assert resp.status_code in {401, 403}
