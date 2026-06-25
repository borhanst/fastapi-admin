"""Protocol for user models that can be used as the admin auth model."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AdminUserProtocol(Protocol):
    """
    Any user model passed as auth_model= must satisfy this interface.
    These are the only attributes the admin framework reads from the user object.
    """

    id: int | str  # primary key (any type)
    email: str  # used for audit log denormalization
    is_active: bool  # inactive users are refused login
    is_superuser: bool  # bypasses all permission checks if True

    # Role linkage — the admin reads this to look up permissions.
    # Must be either:
    #   (a) an integer FK to admin_roles.id (simplest)
    #   (b) None — then the user has no role and all permissions default to False
    role_id: int | None
