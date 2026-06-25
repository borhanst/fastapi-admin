"""SQLAlchemy models for admin auth: roles, users, permissions, field permissions."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from fastapi_console.models.base import Base


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("AdminUser", back_populates="role")
    permissions = relationship(
        "AdminPermission", back_populates="role", cascade="all, delete-orphan"
    )
    field_permissions = relationship(
        "AdminFieldPermission", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AdminRole {self.name!r}>"


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role_id = Column(Integer, ForeignKey("admin_roles.id"), nullable=True)
    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    role = relationship("AdminRole", back_populates="users")

    def __repr__(self) -> str:
        return f"<AdminUser {self.email!r}>"


class AdminPermission(Base):
    __tablename__ = "admin_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "table_name", name="uq_admin_perm_role_table"),
    )

    id = Column(Integer, primary_key=True)
    role_id = Column(
        Integer,
        ForeignKey("admin_roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_name = Column(String(255), nullable=False)
    can_view = Column(Boolean, default=False)
    can_create = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)

    role = relationship("AdminRole", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<AdminPermission role={self.role_id} table={self.table_name!r}>"


class AdminFieldPermission(Base):
    __tablename__ = "admin_field_permissions"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "table_name",
            "field_name",
            name="uq_admin_field_perm_role_table_field",
        ),
    )

    id = Column(Integer, primary_key=True)
    role_id = Column(
        Integer,
        ForeignKey("admin_roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_name = Column(String(255), nullable=False)
    field_name = Column(String(255), nullable=False)
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=True)

    role = relationship("AdminRole", back_populates="field_permissions")

    def __repr__(self) -> str:
        return (
            f"<AdminFieldPermission role={self.role_id} "
            f"table={self.table_name!r} field={self.field_name!r}>"
        )
