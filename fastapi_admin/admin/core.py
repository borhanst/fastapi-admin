"""Admin class — public API, wires everything at init."""

from __future__ import annotations

import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment

from fastapi_admin.admin.admin_config import AdminConfig
from fastapi_admin.admin.admin_database import AdminDatabase
from fastapi_admin.admin.admin_router import AdminRouter
from fastapi_admin.admin.admin_template import AdminTemplate
from fastapi_admin.config import (
    AuditConfig,
    AuthConfig,
    BehaviorConfig,
    NavConfig,
    StorageConfig,
    UIConfig,
)
from fastapi_admin.exceptions import ConfigError
from fastapi_admin.registry import AdminRegistry, RegisteredModel
from fastapi_admin.types import SeedRole

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from fastapi_admin.auth.backend import AuthBackend
    from fastapi_admin.nav import NavGroupConfig, SidebarBuilder
    from fastapi_admin.storage.base import StorageBackend
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

    Uses component-based architecture with:
    - config: AdminConfig (UI, auth, audit, behavior, storage, nav settings)
    - database: AdminDatabase (engine, table creation, role seeding)
    - router: AdminRouter (routing, static files, Jinja)
    - template: AdminTemplate (branding, sidebar context)
    """

    def __init__(
        self,
        app: FastAPI | None = None,
        engine: Engine | None = None,
        *,
        # Component instances (new API)
        config: AdminConfig | None = None,
        database: AdminDatabase | None = None,
        router: AdminRouter | None = None,
        template: AdminTemplate | None = None,
        # Legacy kwargs for backward compatibility
        base: type | None = None,
        title: str = "FastAPI Admin",
        logo_url: str | None = None,
        favicon_url: str | None = None,
        primary_color: str = "#0ea5e9",
        primary_color_dark: str = "#0284c7",
        dark_mode_default: bool = False,
        per_page_default: int = 25,
        session_ttl: int = 28800,
        audit_retention_days: int = 365,
        dashboard_stats: list[str] | None = None,
        dashboard_charts: bool = True,
        admin_path: str = "/admin",
        secret_key: str = "",
        auth_model: type | None = None,
        auth_backend: AuthBackend | None = None,
        session_cookie_name: str = "admin_session",
        session_secure: bool = False,
        seed_roles: list[SeedRole] | None = None,
        seed_roles_overwrite: bool = False,
        superuser_emails: list[str] | None = None,
        storage: StorageBackend | None = None,
        uploads_url: str = "/uploads",
        auto_discover: bool = True,
        nav_groups: list[NavGroupConfig] | None = None,
        sidebar_builder: SidebarBuilder | None = None,
        require_tags: bool = False,
    ):
        self.registry = AdminRegistry()
        self._app: FastAPI | None = app

        # Build components from legacy kwargs if components not provided
        if config is None:
            config = AdminConfig(
                ui=UIConfig(
                    title=title,
                    logo_url=logo_url,
                    favicon_url=favicon_url,
                    primary_color=primary_color,
                    primary_color_dark=primary_color_dark,
                    dark_mode_default=dark_mode_default,
                    per_page_default=per_page_default,
                ),
                auth=AuthConfig(
                    auth_model=auth_model,
                    auth_backend=auth_backend,
                    session_ttl=session_ttl,
                    session_cookie_name=session_cookie_name,
                    session_secure=session_secure,
                    superuser_emails=superuser_emails,
                ),
                audit=AuditConfig(audit_retention_days=audit_retention_days),
                behavior=BehaviorConfig(
                    auto_discover=auto_discover,
                    dashboard_stats=dashboard_stats or [],
                    dashboard_charts=dashboard_charts,
                ),
                storage=StorageConfig(storage=storage, uploads_url=uploads_url),
                nav=NavConfig(
                    nav_groups=nav_groups or [],
                    sidebar_builder=sidebar_builder,
                    require_tags=require_tags,
                ),
            )

        if database is None:
            database = AdminDatabase(engine=engine, base=base)

        if router is None:
            router = AdminRouter(
                admin_path=admin_path,
                secret_key=secret_key or os.environ.get("SECRET_KEY", ""),
            )

        if template is None:
            template = AdminTemplate(
                title=config.ui.title,
                logo_url=config.ui.logo_url,
                favicon_url=config.ui.favicon_url,
                primary_color=config.ui.primary_color,
                primary_color_dark=config.ui.primary_color_dark,
                dark_mode_default=config.ui.dark_mode_default,
            )

        self.config = config
        self.database = database
        self.router = router
        self.template = template

        # RBAC
        self.seed_roles = (
            seed_roles if seed_roles is not None else DEFAULT_SEED_ROLES
        )
        self.seed_roles_overwrite = seed_roles_overwrite

        # Built sidebar (populated during setup)
        self._nav_groups_built: list[Any] = []

        # Internal state (populated during setup)
        self._session_backend: Any = None
        self._jinja_env: Environment | None = None
        self._router_built: bool = False

        if app is not None and engine is not None:
            # Deferred setup — user will call await admin.setup() via lifespan
            pass

    # ------------------------------------------------------------------
    # Backward-compatible property accessors
    # ------------------------------------------------------------------

    @property
    def title(self) -> str:
        return self.config.ui.title

    @property
    def logo_url(self) -> str | None:
        return self.config.ui.logo_url

    @property
    def favicon_url(self) -> str | None:
        return self.config.ui.favicon_url

    @property
    def primary_color(self) -> str:
        return self.config.ui.primary_color

    @property
    def primary_color_dark(self) -> str:
        return self.config.ui.primary_color_dark

    @property
    def dark_mode_default(self) -> bool:
        return self.config.ui.dark_mode_default

    @property
    def per_page_default(self) -> int:
        return self.config.ui.per_page_default

    @property
    def admin_path(self) -> str:
        return self.router.admin_path

    @property
    def secret_key(self) -> str:
        return self.router.secret_key

    @property
    def engine(self) -> Engine | None:
        return self.database.engine

    @property
    def base(self) -> type | None:
        return self.database.base

    @property
    def session_ttl(self) -> int:
        return self.config.auth.session_ttl

    @property
    def audit_retention_days(self) -> int:
        return self.config.audit.audit_retention_days

    @property
    def dashboard_stats(self) -> list[str]:
        return self.config.behavior.dashboard_stats

    @property
    def dashboard_charts(self) -> bool:
        return self.config.behavior.dashboard_charts

    @property
    def auth_model(self) -> type | None:
        return self.config.auth.auth_model

    @property
    def auth_backend(self) -> AuthBackend | None:
        return self.config.auth.auth_backend

    @property
    def session_cookie_name(self) -> str:
        return self.config.auth.session_cookie_name

    @property
    def session_secure(self) -> bool:
        return self.config.auth.session_secure

    @property
    def superuser_emails(self) -> list[str]:
        return self.config.auth.superuser_emails

    @property
    def storage(self) -> StorageBackend | None:
        return self.config.storage.storage

    @property
    def uploads_url(self) -> str:
        return self.config.storage.uploads_url

    @property
    def auto_discover(self) -> bool:
        return self.config.behavior.auto_discover

    @property
    def nav_groups(self) -> list[NavGroupConfig]:
        return self.config.nav.nav_groups

    @property
    def sidebar_builder(self) -> SidebarBuilder | None:
        return self.config.nav.sidebar_builder

    @property
    def require_tags(self) -> bool:
        return self.config.nav.require_tags

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

        if self.database.engine is None:
            raise ConfigError(
                "Admin requires a SQLAlchemy engine. Pass engine= to Admin()."
            )

        app = self._app

        # 1. Validate auth_model satisfies AdminUserProtocol
        self.config.auth.validate_auth_model()

        # 2. Database tables should be created via Alembic migrations
        skip_create_tables = (
            os.environ.get("SKIP_CREATE_TABLES", "true").lower() == "true"
        )
        if not skip_create_tables:
            await self.database._create_tables()

        # 3. Seed default roles
        await self.database._seed_roles(
            self.seed_roles, self.seed_roles_overwrite
        )

        # 4. Create and store session backend
        self._session_backend = self.database._init_session_backend(
            secret_key=self.router.secret_key,
            session_ttl=self.config.auth.session_ttl,
            cookie_name=self.config.auth.session_cookie_name,
            secure=self.config.auth.session_secure,
        )

        # 5. Store backends and config on app.state
        self._wire_app_state(app)

        # 6. Mount static files
        self._mount_static(app)

        # 7. Initialise Jinja2
        self._init_jinja(app)

        # 8. Auto-discover models
        if self.config.behavior.auto_discover:
            self.registry.auto_discover()

        # 9. Validate require_tags
        if self.config.nav.require_tags:
            self._validate_tags()

        # 10. Build sidebar structure (once at startup)
        self._nav_groups_built = self._build_sidebar()
        self.template._nav_groups_built = self._nav_groups_built
        if self._jinja_env:
            self._jinja_env.env.globals["nav_groups"] = self._nav_groups_built

        # 11. Build and mount routers
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
            registered = self.registry.register(model, admin_class)
        else:
            registered = self.registry.register(model)
        if self._jinja_env:
            self._jinja_env.env.globals["registered_models"] = (
                self.registry.all()
            )
            if self._nav_groups_built:
                self._nav_groups_built = self._build_sidebar()
                self.template._nav_groups_built = self._nav_groups_built
                self._jinja_env.env.globals["nav_groups"] = (
                    self._nav_groups_built
                )
        if admin_class is not None:
            return registered
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
        self.config.auth.validate_auth_model()

    def _wire_app_state(self, app: FastAPI) -> None:
        """Store backends and configuration on app.state as typed AdminState."""
        from fastapi_admin.admin.state import AdminState

        admin_config = {
            "title": self.config.ui.title,
            "logo_url": self.config.ui.logo_url,
            "favicon_url": self.config.ui.favicon_url,
            "primary_color": self.config.ui.primary_color,
            "primary_color_dark": self.config.ui.primary_color_dark,
            "dark_mode_default": self.config.ui.dark_mode_default,
            "per_page_default": self.config.ui.per_page_default,
            "session_ttl": self.config.auth.session_ttl,
            "audit_retention_days": self.config.audit.audit_retention_days,
            "dashboard_stats": self.config.behavior.dashboard_stats,
            "dashboard_charts": self.config.behavior.dashboard_charts,
            "admin_path": self.router.admin_path,
            "superuser_emails": self.config.auth.superuser_emails,
        }

        # Create async session if engine is async, else None
        db_session = None
        engine = self.database.engine
        if engine is not None:
            from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

            if isinstance(engine, AsyncEngine):
                db_session = AsyncSession(engine, expire_on_commit=False)

        state = AdminState(
            engine=engine,
            session_backend=self._session_backend,
            auth_backend=self.config.auth.auth_backend,
            storage=self.config.storage.storage,
            registry=self.registry,
            db_session=db_session,
            config=admin_config,
            jinja_env=self._jinja_env,
            admin_instance=self,
        )

        # Store typed state as single attribute
        app.state.admin_state = state

        # Also store individual attributes for backward compatibility
        app.state.admin = self  # Admin instance (backward compat)
        app.state.admin_engine = state.engine
        app.state.admin_session_backend = state.session_backend
        app.state.admin_auth_backend = state.auth_backend
        app.state.admin_storage = state.storage
        app.state.admin_registry = state.registry
        app.state.admin_db_session = state.db_session
        app.state.admin_config = state.config
        app.state.admin_jinja_env = state.jinja_env

    def _mount_static(self, app: FastAPI) -> None:
        """Mount the static files directory and uploads directory."""
        static_dir = Path(__file__).parent.parent / "static"
        if static_dir.is_dir():
            app.mount(
                "/static",
                StaticFiles(directory=str(static_dir)),
                name="admin_static",
            )

        # Mount uploads directory if using LocalStorageBackend
        from fastapi_admin.storage.local import LocalStorageBackend

        if isinstance(self.config.storage.storage, LocalStorageBackend):
            self.config.storage.storage.ensure_dir()
            app.mount(
                self.config.storage.uploads_url,
                StaticFiles(
                    directory=str(self.config.storage.storage.upload_dir)
                ),
                name="admin_uploads",
            )

    def _init_jinja(self, app: FastAPI) -> None:
        """Initialise the Jinja2 template environment."""
        from starlette.templating import Jinja2Templates

        templates_dir = Path(__file__).parent.parent / "templates"
        self._jinja_env = Jinja2Templates(directory=str(templates_dir))
        slugify = lambda s: (
            re.sub(r"[^\w]", "-", s, flags=re.A).strip("-").lower()
        )
        self._jinja_env.env.filters["slugify"] = slugify
        self._jinja_env.env.globals["registered_models"] = self.registry.all()
        self._jinja_env.env.globals["admin_path"] = self.router.admin_path
        self._jinja_env.env.globals["nav_groups"] = self._nav_groups_built
        app.state.admin_jinja_env = self._jinja_env

    def _build_router(self, app: FastAPI) -> None:
        """Build and mount routers for all registered models."""
        if self._router_built:
            return

        from fastapi_admin.auth.router import router as auth_router
        from fastapi_admin.router import build_model_router
        from fastapi_admin.views.audit import router as audit_router
        from fastapi_admin.views.roles import router as roles_router

        for registered in self.registry.all():
            model_router = build_model_router(registered)
            app.include_router(model_router, prefix=self.router.admin_path)

        # Auth routes (login/logout)
        app.include_router(auth_router, prefix=self.router.admin_path)

        # Audit & role management routes
        app.include_router(audit_router, prefix=self.router.admin_path)
        app.include_router(roles_router, prefix=self.router.admin_path)

        # Dashboard route
        from fastapi_admin.views.dashboard import dashboard_view_factory

        dashboard_view = dashboard_view_factory(self)
        app.add_api_route(
            self.router.admin_path,
            dashboard_view,
            methods=["GET"],
            tags=["admin"],
        )

        # JSON API for external frontend apps
        from fastapi_admin.api import AdminAPIRouter

        api_router = AdminAPIRouter(registry=self.registry)
        app.include_router(api_router.build_router())

        self._router_built = True

    # ------------------------------------------------------------------
    # Tags validation
    # ------------------------------------------------------------------

    def _validate_tags(self) -> None:
        """Raise ConfigError if any registered model has no tag (when require_tags=True)."""
        untagged: list[str] = []
        for registered in self.registry.all():
            admin = registered.admin
            tags = getattr(admin, "tags", None)
            tag = getattr(admin, "tag", None)
            if not tags and not tag:
                untagged.append(registered.table_name)
        if untagged:
            raise ConfigError(
                "require_tags=True but the following models have no tag: "
                + ", ".join(sorted(untagged))
            )

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _build_sidebar(self) -> list:
        """Build the sidebar group structure once at startup."""
        from fastapi_admin.nav import DefaultSidebarBuilder

        builder = self.config.nav.sidebar_builder or DefaultSidebarBuilder()
        return builder.build(
            self.registry.all(),
            self.config.nav.nav_groups,
            admin_path=self.router.admin_path,
        )

    def build_sidebar_context(self, request: Any, user: Any = None) -> dict:
        """Build per-request sidebar context (RBAC filter + permissions map)."""
        return self.template.build_sidebar_context(request, user=user)

    def sidebar_template_kwargs(self, request: Any) -> dict[str, Any]:
        """Thin wrapper — returns sidebar kwargs for TemplateResponse contexts."""
        return self.template.sidebar_template_kwargs(request)

    def apply_sidebar_context(
        self, request: Any, user: Any, context: dict
    ) -> dict:
        """Inject nav_groups + permissions_map into a template context dict."""
        return self.template.apply_sidebar_context(request, user, context)
