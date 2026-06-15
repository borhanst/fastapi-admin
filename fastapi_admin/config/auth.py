"""Authentication configuration."""

from typing import TYPE_CHECKING, Any

from fastapi_admin.exceptions import ConfigError

if TYPE_CHECKING:
    pass


class AuthConfig:
    """Authentication configuration."""

    def __init__(
        self,
        auth_model: type | None = None,
        auth_backend: Any | None = None,
        session_ttl: int = 28800,
        session_cookie_name: str = "admin_session",
        session_secure: bool = False,
        superuser_emails: list[str] | None = None,
    ):
        self.auth_model = auth_model
        self.auth_backend = auth_backend
        self.session_ttl = session_ttl
        self.session_cookie_name = session_cookie_name
        self.session_secure = session_secure
        self.superuser_emails = superuser_emails or []

    def validate_auth_model(self) -> None:
        """Validate that auth_model satisfies AdminUserProtocol."""
        model = self.auth_model
        if model is None:
            return

        required_attrs = ["id", "email", "is_active", "is_superuser", "role_id"]
        missing = [attr for attr in required_attrs if not hasattr(model, attr)]
        if missing:
            raise ConfigError(
                f"auth_model {model.__name__!r} does not satisfy AdminUserProtocol. "
                f"Missing attributes: {', '.join(missing)}"
            )