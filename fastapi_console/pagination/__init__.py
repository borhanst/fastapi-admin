"""Pagination strategies for FastAPI Console."""

from fastapi_console.pagination.base import BasePagination, PaginationResult
from fastapi_console.pagination.cursor import CursorPagination
from fastapi_console.pagination.dynamic import DynamicPagination
from fastapi_console.pagination.offset import OffsetPagination

__all__ = [
    "BasePagination",
    "PaginationResult",
    "OffsetPagination",
    "CursorPagination",
    "DynamicPagination",
]
