"""Token-based authentication for the Admin JSON API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import APIRouter, HTTPException, Request

from fastapi_admin.api.schemas import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["api-auth"])


def _get_secret_key(request: Request) -> str:
    """Get the JWT signing key from the unified signing-key source.

    Reads ``app.state.admin_secret_key`` (the same key the signed-cookie
    sessions and CSRF use). Fails closed with 500 if unset — JWT signing
    must never silently fall back to a known constant.
    """
    secret_key = getattr(request.app.state, "admin_secret_key", "")
    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail="JWT signing key not configured — admin secret_key not set.",
        )
    return secret_key


def _get_token_ttl(request: Request) -> int:
    """Get token TTL in seconds from admin config."""
    config = getattr(request.app.state, "admin_config", {})
    return config.get("session_ttl", 28800)


def create_access_token(
    user_id: int | str,
    secret_key: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    expire = datetime.now(UTC) + (expires_delta or timedelta(hours=24))
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(token: str, secret_key: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token. Returns payload or None."""
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


@router.post("/token", response_model=TokenResponse)
async def obtain_token(
    request: Request,
    body: TokenRequest,
) -> TokenResponse:
    """POST /api/auth/token — obtain a JWT access token.

    Authenticate with email/password and receive a Bearer token
    for use with all other API endpoints.
    """
    auth_backend = getattr(request.app.state, "admin_auth_backend", None)
    if auth_backend is None:
        raise HTTPException(
            status_code=500, detail="Auth backend not configured."
        )

    db_session = getattr(request.app.state, "admin_db_session", None)
    if db_session is None:
        raise HTTPException(
            status_code=500, detail="Database session not available."
        )

    user = await auth_backend.authenticate(
        body.email, body.password, db_session
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    secret_key = _get_secret_key(request)
    ttl = _get_token_ttl(request)
    token = create_access_token(
        user.id, secret_key, expires_delta=timedelta(seconds=ttl)
    )

    return TokenResponse(access_token=token)
