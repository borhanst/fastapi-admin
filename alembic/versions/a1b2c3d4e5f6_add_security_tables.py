"""add security tables

Revision ID: a1b2c3d4e5f6
Revises: 90756d9f5ed1
Create Date: 2026-06-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "90756d9f5ed1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add password_changed_at, refresh tokens, TOTP, and login attempts tables."""
    # Add password_changed_at to admin_users
    op.add_column(
        "admin_users",
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "admin_users",
        sa.Column("is_superuser", sa.Boolean(), nullable=True),
    )

    # Create admin_refresh_tokens table
    op.create_table(
        "admin_refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["admin_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "token_hash", name="uq_admin_refresh_token"),
    )
    op.create_index(
        "ix_admin_refresh_tokens_token_hash",
        "admin_refresh_tokens",
        ["token_hash"],
    )

    # Create admin_user_totp table
    op.create_table(
        "admin_user_totp",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("secret_key", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("backup_codes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["admin_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # Create admin_login_attempts table
    op.create_table(
        "admin_login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_login_attempts_email",
        "admin_login_attempts",
        ["email"],
    )


def downgrade() -> None:
    """Remove security tables and columns."""
    op.drop_index("ix_admin_login_attempts_email", "admin_login_attempts")
    op.drop_table("admin_login_attempts")
    op.drop_table("admin_user_totp")
    op.drop_index("ix_admin_refresh_tokens_token_hash", "admin_refresh_tokens")
    op.drop_table("admin_refresh_tokens")
    op.drop_column("admin_users", "is_superuser")
    op.drop_column("admin_users", "password_changed_at")
