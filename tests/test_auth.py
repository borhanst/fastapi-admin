"""Tests for Phase 7 — Auth Backend & Session."""

import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fastapi_admin.auth.backend import AuthBackend, BuiltinAuthBackend, _PasswordHasher
from fastapi_admin.auth.models import AdminRole, AdminUser
from fastapi_admin.auth.session import SessionBackend, SignedCookieSessionBackend
from fastapi_admin.models import Base


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
def session_backend():
    return SignedCookieSessionBackend(secret_key="test-secret-key", session_ttl=3600)


@pytest.fixture
def role(session):
    role = AdminRole(name="Editor")
    session.add(role)
    session.flush()
    return role


@pytest.fixture
def user(session, role):
    user = AdminUser(
        email="admin@example.com",
        hashed_password=_PasswordHasher.hash("secret123"),
        full_name="Test Admin",
        role_id=role.id,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


# ---------------------------------------------------------------------------
# 7.1 — SessionBackend ABC
# ---------------------------------------------------------------------------


class TestSessionBackendABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            SessionBackend()  # type: ignore[abstract]

    def test_subclass_must_implement_encode_decode(self):
        class Incomplete(SessionBackend):
            pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]

    def test_concrete_subclass_works(self):
        class Concrete(SessionBackend):
            def encode(self, payload):
                return "encoded"

            def decode(self, token):
                return {"user_id": 1}

        sb = Concrete()
        assert sb.encode({"user_id": 1}) == "encoded"
        assert sb.decode("token") == {"user_id": 1}


# ---------------------------------------------------------------------------
# 7.2 — SignedCookieSessionBackend round-trip
# ---------------------------------------------------------------------------


class TestSignedCookieSessionBackend:
    def test_encode_decode_round_trip(self, session_backend):
        payload = {"user_id": 42, "issued_at": int(time.time())}
        token = session_backend.encode(payload)
        decoded = session_backend.decode(token)
        assert decoded == payload

    def test_decode_returns_none_for_none(self, session_backend):
        assert session_backend.decode(None) is None

    def test_decode_returns_none_for_empty_string(self, session_backend):
        assert session_backend.decode("") is None

    def test_decode_returns_none_for_tampered_token(self, session_backend):
        token = session_backend.encode({"user_id": 1})
        tampered = token[:-5] + "XXXXX"
        assert session_backend.decode(tampered) is None

    def test_decode_returns_none_for_wrong_secret(self, session_backend):
        other = SignedCookieSessionBackend(secret_key="different-key")
        token = session_backend.encode({"user_id": 1})
        assert other.decode(token) is None

    def test_decode_returns_none_for_expired_token(self):
        short_ttl = SignedCookieSessionBackend(
            secret_key="test-key", session_ttl=1
        )
        token = short_ttl.encode({"user_id": 1})
        time.sleep(2)
        assert short_ttl.decode(token) is None

    def test_custom_cookie_name(self):
        sb = SignedCookieSessionBackend(
            secret_key="k", cookie_name="my_cookie"
        )
        assert sb.cookie_name == "my_cookie"

    def test_default_cookie_name(self, session_backend):
        assert session_backend.cookie_name == "admin_session"

    def test_secure_default_false(self, session_backend):
        assert session_backend.secure is False

    def test_secure_set_true(self):
        sb = SignedCookieSessionBackend(secret_key="k", secure=True)
        assert sb.secure is True


# ---------------------------------------------------------------------------
# 7.3 — AuthBackend ABC
# ---------------------------------------------------------------------------


class TestAuthBackendABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            AuthBackend()  # type: ignore[abstract]

    def test_subclass_must_implement_methods(self):
        class Incomplete(AuthBackend):
            pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# 7.4 — BuiltinAuthBackend
# ---------------------------------------------------------------------------


class TestBuiltinAuthBackend:
    @pytest.fixture
    def backend(self):
        return BuiltinAuthBackend()

    @pytest.mark.asyncio
    async def test_authenticate_success(self, backend, session, user):
        result = await backend.authenticate("admin@example.com", "secret123", session)
        assert result is not None
        assert result.email == "admin@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, backend, session, user):
        result = await backend.authenticate("admin@example.com", "wrong", session)
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_unknown_email(self, backend, session, user):
        result = await backend.authenticate("nobody@example.com", "secret123", session)
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, backend, session, user):
        user.is_active = False
        session.flush()
        result = await backend.authenticate("admin@example.com", "secret123", session)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_success(self, backend, session, user):
        result = await backend.get_user(user.id, session)
        assert result is not None
        assert result.email == "admin@example.com"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, backend, session):
        result = await backend.get_user(99999, session)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_inactive(self, backend, session, user):
        user.is_active = False
        session.flush()
        result = await backend.get_user(user.id, session)
        assert result is None


# ---------------------------------------------------------------------------
# 7.4 — pwd_context hash/verify
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = _PasswordHasher.hash("mypassword")
        assert _PasswordHasher.verify("mypassword", hashed)

    def test_wrong_password_fails(self):
        hashed = _PasswordHasher.hash("mypassword")
        assert not _PasswordHasher.verify("wrongpassword", hashed)

    def test_different_hashes(self):
        h1 = _PasswordHasher.hash("same")
        h2 = _PasswordHasher.hash("same")
        assert h1 != h2
