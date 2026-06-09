"""Auth backend — ABC + built-in implementation."""

from __future__ import annotations

import bcrypt
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from fastapi_admin.auth.protocol import AdminUserProtocol


class _PasswordHasher:
    """Thin wrapper around bcrypt for hash/verify."""

    @staticmethod
    def hash(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except (ValueError, TypeError):
            return False


pwd_context = _PasswordHasher()


class AuthBackend(ABC):
    """Abstract authentication backend — verify credentials & load users."""

    @abstractmethod
    async def authenticate(
        self, email: str, password: str, session: Any
    ) -> AdminUserProtocol | None:
        """Verify credentials. Return user object if valid, ``None`` otherwise."""
        ...

    @abstractmethod
    async def get_user(self, user_id: int | str, session: Any) -> AdminUserProtocol | None:
        """Load user by PK. Return ``None`` if not found or inactive."""
        ...


class BuiltinAuthBackend(AuthBackend):
    """Default backend that works with the built-in ``AdminUser`` model."""

    async def authenticate(
        self, email: str, password: str, session: Session
    ) -> AdminUserProtocol | None:
        from fastapi_admin.auth.models import AdminUser

        user = session.query(AdminUser).filter_by(email=email, is_active=True).first()
        if not user:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user

    async def get_user(self, user_id: int | str, session: Session) -> AdminUserProtocol | None:
        from fastapi_admin.auth.models import AdminUser

        return (
            session.query(AdminUser)
            .filter_by(id=user_id, is_active=True)
            .first()
        )
