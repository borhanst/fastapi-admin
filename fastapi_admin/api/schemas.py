"""Pydantic schemas for the Admin JSON API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TokenRequest(BaseModel):
    """Request body for token authentication."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Response containing an access token."""

    access_token: str
    token_type: str = "bearer"


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = 1
    per_page: int = 25
    q: str = ""
    order: str = ""


class PaginatedResponse(BaseModel):
    """Paginated list response."""

    items: list[Any]
    total: int
    page: int
    per_page: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
