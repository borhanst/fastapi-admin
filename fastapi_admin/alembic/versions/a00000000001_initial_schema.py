"""initial admin schema

Revision ID: a00000000001
Revises:
Create Date: 2026-06-25 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a00000000001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create admin tables."""
    # Roles
    op.create_table(
        "admin_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Users
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("admin_roles.id"),
            nullable=True,
        ),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "password_changed_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Table permissions
    op.create_table(
        "admin_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("admin_roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("table_name", sa.String(255), nullable=False),
        sa.Column("can_view", sa.Boolean(), default=False),
        sa.Column("can_create", sa.Boolean(), default=False),
        sa.Column("can_edit", sa.Boolean(), default=False),
        sa.Column("can_delete", sa.Boolean(), default=False),
        sa.UniqueConstraint(
            "role_id", "table_name", name="uq_admin_perm_role_table"
        ),
    )

    # Field permissions
    op.create_table(
        "admin_field_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("admin_roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("table_name", sa.String(255), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("can_view", sa.Boolean(), default=True),
        sa.Column("can_edit", sa.Boolean(), default=True),
        sa.UniqueConstraint(
            "role_id",
            "table_name",
            "field_name",
            name="uq_admin_field_perm_role_table_field",
        ),
    )

    # Refresh tokens (JWT)
    op.create_table(
        "admin_refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("admin_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "user_id", "token_hash", name="uq_admin_refresh_token"
        ),
    )

    # TOTP (2FA)
    op.create_table(
        "admin_user_totp",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("admin_users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("secret_key", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), default=False),
        sa.Column("backup_codes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Login attempts (rate limiting)
    op.create_table(
        "admin_login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("success", sa.Boolean(), default=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Audit log
    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("admin_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("action", sa.String(10), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("table_name", sa.String(255), nullable=False),
        sa.Column("object_id", sa.String(255), nullable=False),
        sa.Column("object_repr", sa.String(500), nullable=True),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("full_snapshot", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_audit_model", "admin_audit_log", ["model_name", "table_name"]
    )
    op.create_index("idx_audit_user", "admin_audit_log", ["user_id"])
    op.create_index("idx_audit_timestamp", "admin_audit_log", ["timestamp"])
    op.create_index(
        "idx_audit_object", "admin_audit_log", ["table_name", "object_id"]
    )


def downgrade() -> None:
    """Drop admin tables."""
    op.drop_table("admin_audit_log")
    op.drop_table("admin_login_attempts")
    op.drop_table("admin_user_totp")
    op.drop_table("admin_refresh_tokens")
    op.drop_table("admin_field_permissions")
    op.drop_table("admin_permissions")
    op.drop_table("admin_users")
    op.drop_table("admin_roles")
