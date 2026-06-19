"""Auth views — login, logout."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_admin.auth.csrf import CSRF_COOKIE_NAME, require_csrf_token
from fastapi_admin.auth.dependencies import _get_db_session, get_session

router = APIRouter()


def _is_safe_url(url: str | None) -> bool:
    """Return True if the URL is relative (no scheme or netloc)."""
    if not url:
        return False
    parsed = urlparse(url)
    return not (parsed.scheme or parsed.netloc)


@router.get("/login", response_class=HTMLResponse)
async def login_get(
    request: Request,
    next: str | None = None,
    session_payload: dict[str, Any] | None = Depends(get_session),
) -> HTMLResponse:
    """GET /admin/login — show login page, redirect if already logged in."""
    if session_payload is not None:
        target = next if _is_safe_url(next) else "/admin/"
        return RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)

    jinja_env = request.app.state.admin_jinja_env
    template = jinja_env.get_template("pages/login.html")
    csrf_token = getattr(request.state, "csrf_token", "")
    return HTMLResponse(template.render({
        "request": request,
        "csrf_token": csrf_token,
    }))


@router.post("/login", response_model=None)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str | None = Form(None),
    session: AsyncSession = Depends(_get_db_session),
    _csrf: bool = Depends(require_csrf_token),
) -> HTMLResponse | RedirectResponse:
    """POST /admin/login — process login form."""
    auth_backend = request.app.state.admin_auth_backend
    user = await auth_backend.authenticate(email, password, session)
    if user is not None:
        user.last_login = datetime.now(UTC)
        await session.merge(user)
        await session.commit()

        session_backend = request.app.state.admin_session_backend
        session_data = {"user_id": user.id}
        token = session_backend.encode(session_data)

        if next and _is_safe_url(next):
            redirect_url = next
        else:
            redirect_url = "/admin/"

        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_302_FOUND
        )
        response.set_cookie(
            key=session_backend.cookie_name,
            value=token,
            max_age=session_backend._session_ttl,
            path="/",
            secure=session_backend.secure,
            httponly=True,
            samesite="lax",
        )
        return response

    # Login failed — re-render with error
    jinja_env = request.app.state.admin_jinja_env
    template = jinja_env.get_template("pages/login.html")
    csrf_token = getattr(request.state, "csrf_token", "")
    return HTMLResponse(
        template.render({
            "request": request,
            "error": "Invalid email or password. Please try again.",
            "csrf_token": csrf_token,
        }),
        status_code=status.HTTP_200_OK,
    )


@router.post("/logout")
async def logout_post(
    request: Request,
    session_payload: dict[str, Any] | None = Depends(get_session),
    _csrf: bool = Depends(require_csrf_token),
) -> RedirectResponse:
    """POST /admin/logout — clear session and redirect to login."""
    if session_payload is not None:
        auth_backend = request.app.state.admin_auth_backend
        if hasattr(auth_backend, "on_logout"):
            await auth_backend.on_logout(session_payload.get("user_id"))

    session_backend = request.app.state.admin_session_backend
    response = RedirectResponse(
        url="/admin/login", status_code=status.HTTP_302_FOUND
    )
    response.delete_cookie(
        key=session_backend.cookie_name,
        path="/",
        secure=session_backend.secure,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
    )
    return response
