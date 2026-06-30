
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fastapi_console.models.base import Base as AdminBase
from tests.test_registry import Product


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    AdminBase.metadata.create_all(engine)
    Product.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def app():
    from fastapi import FastAPI
    return FastAPI()


@pytest.fixture
def admin_user(engine):
    from sqlalchemy.orm import sessionmaker
    from fastapi_console.auth.models import AdminRole, AdminUser

    SessionLocal = sessionmaker(engine)
    session = SessionLocal()
    try:
        role = AdminRole(name="SuperAdmin")
        session.add(role)
        session.flush()
        user = AdminUser(
            email="admin@test.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            full_name="Admin",
            is_superuser=True,
            is_active=True,
        )
        user.roles.append(role)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


@pytest.fixture
def admin_app(app, engine, admin_user):
    from fastapi_console import Admin
    admin = Admin(app=app, engine=engine, secret_key="test-secret-key-long-enough-for-security!", auto_discover=False)
    return app
