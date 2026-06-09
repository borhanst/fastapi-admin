"""Admin class — public API, wires everything at init."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from fastapi_admin.exceptions import ConfigError
from fastapi_admin.registry import AdminRegistry, RegisteredModel
from fastapi_admin.types import SeedRole

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from fastapi_admin.auth.backend import AuthBackend
    from fastapi_admin.views import ModelAdmin


# ---------------------------------------------------------------------------
# Default seed roles per AUTH_RBAC_SYSTEM.md §13
# ---------------------------------------------------------------------------

DEFAULT_SEED_ROLES: list[SeedRole] = [
    SeedRole(
        name="SuperAdmin",
        description="Full system access — equivalent to is_superuser=True",
        permissions={},  # empty = all permissions (superuser)
    ),
    SeedRole(
        name="Admin",
        description="Site administration — all permissions except admin_users",
        permissions={
            "admin_users": {
                "view": True,
                "create": False,
                "edit": False,
                "delete": False,
            },
        },
    ),
    SeedRole(
        name="Editor",
        description="Content editing — full CRUD on non-system models",
        permissions={},  # non-system models get full CRUD
    ),
    SeedRole(
        name="Viewer",
        description="Read-only access",
        permissions={},  # view-only for all models
    ),
]


class _RegistrationProxy:
    """Dual-purpose return value from Admin.register().

    Acts as a proxy to the underlying RegisteredModel so attribute access
    (``.model``, ``.admin``, etc.) works transparently.  Also supports
    use as a class decorator::

        @admin.register(Product)
        class ProductAdmin(ModelAdmin): ...

    When called with a class, it re-registers with that admin class and
    returns the resulting RegisteredModel.
    """

    def __init__(self, admin: Admin, registered: RegisteredModel) -> None:
        object.__setattr__(self, "_admin", admin)
        object.__setattr__(self, "_registered", registered)

    def __call__(self, admin_class: type[ModelAdmin]) -> RegisteredModel:
        reg: AdminRegistry = self._admin.registry
        registered = reg.register(self._registered.model, admin_class)
        object.__setattr__(self, "_registered", registered)
        return registered

    def __getattr__(self, name: str) -> Any:
        return getattr(self._registered, name)


class Admin:
    """Main admin interface. Register models and mount to your FastAPI app.

    Full configuration kwargs from ``AUTH_RBAC_SYSTEM.md`` §17 and
    ``fastapi_admin_core_spec.md`` §3.12.
    """

    def __init__(
        self,
        app: FastAPI | None = None,
        engine: Engine | None = None,
        *,
        # Database
        base: type | None = None,  # User's SQLAlchemy DeclarativeBase
        # Branding
        title: str = "FastAPI Admin",
        logo_url: str | None = None,
        favicon_url: str | None = None,
        primary_color: str = "#0ea5e9",
        primary_color_dark: str = "#0284c7",
        # Behavior
        dark_mode_default: bool = False,
        per_page_default: int = 25,
        session_ttl: int = 28800,
        audit_retention_days: int = 365,
        # Dashboard
        dashboard_stats: list[str] | None = None,
        dashboard_charts: bool = True,
        # Security
        admin_path: str = "/admin",
        secret_key: str = "",
        # Auth
        auth_model: type | None = None,
        auth_backend: AuthBackend | None = None,
        session_cookie_name: str = "admin_session",
        session_secure: bool = False,
        # RBAC
        seed_roles: list[SeedRole] | None = None,
        seed_roles_overwrite: bool = False,
        superuser_emails: list[str] | None = None,
        # Behavior flags
        auto_discover: bool = True,
    ):
        self.registry = AdminRegistry()
        self.engine = engine
        self.base = base  # Store user's Base for table creation
        self._app: FastAPI | None = app

        # Branding
        self.title = title
        self.logo_url = logo_url
        self.favicon_url = favicon_url
        self.primary_color = primary_color
        self.primary_color_dark = primary_color_dark

        # Behavior
        self.dark_mode_default = dark_mode_default
        self.per_page_default = per_page_default
        self.session_ttl = session_ttl
        self.audit_retention_days = audit_retention_days

        # Dashboard
        self.dashboard_stats = dashboard_stats or []
        self.dashboard_charts = dashboard_charts

        # Security
        self.admin_path = admin_path.rstrip("/")
        self.secret_key = secret_key or os.environ.get("SECRET_KEY", "")

        # Auth
        self.auth_model = auth_model
        self.auth_backend = auth_backend
        self.session_cookie_name = session_cookie_name
        self.session_secure = session_secure

        # RBAC
        self.seed_roles = (
            seed_roles if seed_roles is not None else DEFAULT_SEED_ROLES
        )
        self.seed_roles_overwrite = seed_roles_overwrite
        self.superuser_emails = superuser_emails or []

        # Flags
        self.auto_discover = auto_discover

        # Internal state (populated during setup)
        self._session_backend: Any = None
        self._jinja_env: Environment | None = None
        self._router_built: bool = False

        if app is not None and engine is not None:
            # Deferred setup — user will call await admin.setup() via lifespan
            pass

    # ------------------------------------------------------------------
    # Setup (async)
    # ------------------------------------------------------------------

    async def setup(self, app: FastAPI | None = None) -> None:
        """Run all startup wiring: create tables, seed roles, mount assets.

        This must be called once during application lifespan, typically via
        the :meth:`lifespan` context manager.
        """
        if app is not None:
            self._app = app

        if self._app is None:
            raise ConfigError(
                "Admin requires a FastAPI app instance. Pass app= or call setup(app=)."
            )

        if self.engine is None:
            raise ConfigError(
                "Admin requires a SQLAlchemy engine. Pass engine= to Admin()."
            )

        app = self._app

        # 1. Validate auth_model satisfies AdminUserProtocol
        self._validate_auth_model()

        # 2. Database tables should be created via Alembic migrations
        # (Skip _create_tables if using migrations)
        skip_create_tables = (
            os.environ.get("SKIP_CREATE_TABLES", "true").lower() == "true"
        )
        if not skip_create_tables:
            await self._create_tables()

        # 3. Seed default roles
        await self._seed_roles()

        # 4. Create and store session backend
        self._init_session_backend()

        # 5. Store backends and config on app.state
        self._wire_app_state(app)

        # 6. Mount static files
        self._mount_static(app)

        # 7. Initialise Jinja2
        self._init_jinja(app)

        # 8. Auto-discover models
        if self.auto_discover:
            self.registry.auto_discover()

        # 9. Build and mount routers
        self._build_router(app)

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------

    def register(
        self,
        model: type,
        admin_class: type[ModelAdmin] | None = None,
    ) -> _RegistrationProxy | RegisteredModel:
        """Register a model with the admin.

        Usage::

            admin.register(Product)

            @admin.register(Product)
            class ProductAdmin(ModelAdmin):
                list_display = ["name", "price"]
        """
        if admin_class is not None:
            return self.registry.register(model, admin_class)

        registered = self.registry.register(model)
        return _RegistrationProxy(self, registered)

    # ------------------------------------------------------------------
    # Lifespan
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        """FastAPI lifespan context manager.

        Usage::

            app = FastAPI(lifespan=admin.lifespan)
        """
        await self.setup(app)
        yield

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_registered(self, table_name: str) -> RegisteredModel | None:
        """Get a registered model by table name."""
        return self.registry.get(table_name)

    def all_registered(self) -> list[RegisteredModel]:
        """Get all registered models."""
        return self.registry.all()

    # ------------------------------------------------------------------
    # Internal wiring
    # ------------------------------------------------------------------

    def _validate_auth_model(self) -> None:
        """Validate that auth_model satisfies AdminUserProtocol."""
        model = self.auth_model
        if model is None:
            # Default — no validation needed, built-in AdminUser is used
            return

        required_attrs = ["id", "email", "is_active", "is_superuser", "role_id"]
        missing = [attr for attr in required_attrs if not hasattr(model, attr)]
        if missing:
            raise ConfigError(
                f"auth_model {model.__name__!r} does not satisfy AdminUserProtocol. "
                f"Missing attributes: {', '.join(missing)}"
            )

    async def _create_tables(self) -> None:
        """Create all admin database tables (async-safe)."""
        from sqlalchemy.ext.asyncio import AsyncEngine

        from fastapi_admin.models.base import Base as AdminBase

        if isinstance(self.engine, AsyncEngine):
            # Async engine - use run_sync
            async with self.engine.begin() as conn:
                # Create admin tables
                await conn.run_sync(AdminBase.metadata.create_all)
                # Create user tables if Base is provided
                if self.base is not None:
                    await conn.run_sync(self.base.metadata.create_all)
        else:
            # Sync engine - direct call
            AdminBase.metadata.create_all(bind=self.engine)
            if self.base is not None:
                self.base.metadata.create_all(bind=self.engine)

    async def _seed_roles(self) -> None:
        """Seed default roles if none exist (or if overwrite is enabled)."""
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
        from sqlalchemy.orm import Session, sessionmaker

        from fastapi_admin.auth.models import AdminPermission, AdminRole

        is_async = isinstance(self.engine, AsyncEngine)

        if is_async:
            # Use AsyncSession for async engine
            SessionLocal = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            async with SessionLocal() as session:
                # Check existing count
                result = await session.execute(select(AdminRole))
                existing_count = len(result.scalars().all())

                if existing_count > 0 and not self.seed_roles_overwrite:
                    return

                if self.seed_roles_overwrite:
                    await session.execute(select(AdminRole).delete())

                for role_spec in self.seed_roles:
                    role = AdminRole(
                        name=role_spec.name, description=role_spec.description
                    )
                    session.add(role)
                    await session.flush()  # get role.id

                    if role_spec.permissions:
                        for table_name, perms in role_spec.permissions.items():
                            perm = AdminPermission(
                                role_id=role.id,
                                table_name=table_name,
                                can_view=perms.get("view", False),
                                can_create=perms.get("create", False),
                                can_edit=perms.get("edit", False),
                                can_delete=perms.get("delete", False),
                            )
                            session.add(perm)

                await session.commit()
        else:
            # Use sync Session for sync engine
            session = Session(bind=self.engine)
            try:
                existing_count = session.query(AdminRole).count()

                if existing_count > 0 and not self.seed_roles_overwrite:
                    return

                if self.seed_roles_overwrite:
                    session.query(AdminRole).delete()

                for role_spec in self.seed_roles:
                    role = AdminRole(
                        name=role_spec.name, description=role_spec.description
                    )
                    session.add(role)
                    session.flush()  # get role.id

                    if role_spec.permissions:
                        for table_name, perms in role_spec.permissions.items():
                            perm = AdminPermission(
                                role_id=role.id,
                                table_name=table_name,
                                can_view=perms.get("view", False),
                                can_create=perms.get("create", False),
                                can_edit=perms.get("edit", False),
                                can_delete=perms.get("delete", False),
                            )
                            session.add(perm)

                session.commit()
            finally:
                session.close()

    def _init_session_backend(self) -> None:
        """Create and store the signed-cookie session backend."""
        from fastapi_admin.auth.session import SignedCookieSessionBackend

        self._session_backend = SignedCookieSessionBackend(
            secret_key=self.secret_key,
            session_ttl=self.session_ttl,
            cookie_name=self.session_cookie_name,
            secure=self.session_secure,
        )

    def _wire_app_state(self, app: FastAPI) -> None:
        """Store backends and configuration on app.state."""
        app.state.admin_engine = self.engine
        app.state.admin_session_backend = self._session_backend
        app.state.admin_auth_backend = self.auth_backend
        app.state.admin_config = {
            "title": self.title,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,
            "primary_color": self.primary_color,
            "primary_color_dark": self.primary_color_dark,
            "dark_mode_default": self.dark_mode_default,
            "per_page_default": self.per_page_default,
            "session_ttl": self.session_ttl,
            "audit_retention_days": self.audit_retention_days,
            "dashboard_stats": self.dashboard_stats,
            "dashboard_charts": self.dashboard_charts,
            "admin_path": self.admin_path,
            "superuser_emails": self.superuser_emails,
        }

    def _mount_static(self, app: FastAPI) -> None:
        """Mount the static files directory."""
        static_dir = Path(__file__).parent / "static"
        if static_dir.is_dir():
            app.mount(
                f"{self.admin_path}/static",
                StaticFiles(directory=str(static_dir)),
                name="admin_static",
            )

    def _init_jinja(self, app: FastAPI) -> None:
        """Initialise the Jinja2 template environment."""
        templates_dir = Path(__file__).parent / "templates"
        loader = FileSystemLoader(str(templates_dir))
        self._jinja_env = Environment(loader=loader, autoescape=True)
        app.state.admin_jinja_env = self._jinja_env

    def _build_router(self, app: FastAPI) -> None:
        """Build and mount routers for all registered models."""
        if self._router_built:
            return

        from fastapi_admin.views import create_model_router

        for registered in self.registry.all():
            model_router = create_model_router(registered)
            app.include_router(model_router, prefix=self.admin_path)

        # Dashboard route
        @app.get(self.admin_path, tags=["admin"])
        async def admin_dashboard():
            from fastapi.responses import HTMLResponse

            models_html = "".join(
                f'<li><a href="{self.admin_path}/{m.table_name}/">{m.verbose_name_plural}</a></li>'
                for m in self.registry.all()
            )
            return HTMLResponse(
                f"<h1>{self.title}</h1><ul>{models_html or '<li>No models registered</li>'}</ul>"
            )

        self._router_built = True
