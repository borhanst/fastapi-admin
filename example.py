"""Example usage of FastAPI Admin with multiple models and configurations."""

import os
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.sql import func

from fastapi_admin import Admin, ModelAdmin
from fastapi_admin.audit.models import (
    AuditLog,  # noqa: F401 — ensure table is created
)
from fastapi_admin.auth.backend import BuiltinAuthBackend
from fastapi_admin.auth.models import AdminUser
from fastapi_admin.models import Base as AdminBase

# ============================================================================
# SQLAlchemy Models
# ============================================================================


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Category(Base):
    """Product category model."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    products = relationship("Product", back_populates="category")

    def __str__(self) -> str:
        return self.name


class Product(Base):
    """Product model with relations."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="products")
    orders = relationship("OrderItem", back_populates="product")

    def __str__(self) -> str:
        return self.name


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    orders = relationship("Order", back_populates="user")

    def __str__(self) -> str:
        return self.email


class Order(Base):
    """Order model."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(
        Enum(
            "pending",
            "processing",
            "completed",
            "cancelled",
            name="order_status",
        ),
        default="pending",
    )
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return f"Order #{self.id}"


class OrderItem(Base):
    """Order line items."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="orders")

    def __str__(self) -> str:
        return f"Item in Order #{self.order_id}"


# ============================================================================
# ModelAdmin Customizations
# ============================================================================


class CategoryAdmin(ModelAdmin):
    """Admin configuration for Category model."""

    list_display = ["id", "name", "created_at"]
    search_fields = ["name"]
    ordering = ["-created_at"]
    verbose_name = "Category"
    verbose_name_plural = "Categories"


class ProductAdmin(ModelAdmin):
    """Admin configuration for Product model."""

    list_display = [
        "id",
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "category"]
    search_fields = ["name", "description"]
    ordering = ["-created_at"]
    fields = ["name", "description", "category", "price", "stock", "is_active"]
    readonly_fields = ["created_at", "updated_at"]
    verbose_name = "Product"
    verbose_name_plural = "Products"
    per_page = 20
    tag = "product"


class UserAdmin(ModelAdmin):
    """Admin configuration for User model."""

    list_display = ["id", "email", "full_name", "is_active", "created_at"]
    search_fields = ["email", "full_name"]
    list_filter = ["is_active"]
    ordering = ["-created_at"]
    fields = ["email", "full_name", "is_active"]
    readonly_fields = ["created_at"]
    verbose_name = "User"
    verbose_name_plural = "Users"
    tag = "user"


class OrderAdmin(ModelAdmin):
    """Admin configuration for Order model."""

    list_display = ["id", "user", "order_date", "status", "total_amount"]
    list_filter = ["status", "order_date"]
    search_fields = ["user__email"]
    ordering = ["-order_date"]
    fields = ["user", "order_date", "status", "total_amount"]
    readonly_fields = ["created_at"]
    verbose_name = "Order"
    verbose_name_plural = "Orders"
    tag = "Order"


# ============================================================================
# FastAPI Application Setup
# ============================================================================

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./example.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def seed_demo_data(session: AsyncSession) -> None:
    """Insert demo data if tables are empty."""
    result = await session.execute(select(Category).limit(1))
    if result.scalars().first() is not None:
        return

    electronics = Category(
        name="Electronics", description="Gadgets and devices"
    )
    clothing = Category(name="Clothing", description="Apparel and accessories")
    session.add_all([electronics, clothing])
    await session.flush()

    products = [
        Product(
            name="Laptop",
            description="15-inch laptop",
            price=999.99,
            stock=50,
            category=electronics,
            is_active=True,
        ),
        Product(
            name="Headphones",
            description="Noise-cancelling",
            price=199.99,
            stock=200,
            category=electronics,
            is_active=True,
        ),
        Product(
            name="T-Shirt",
            description="Cotton tee",
            price=29.99,
            stock=500,
            category=clothing,
            is_active=True,
        ),
        Product(
            name="Jeans",
            description="Slim fit denim",
            price=79.99,
            stock=150,
            category=clothing,
            is_active=False,
        ),
    ]
    session.add_all(products)
    await session.flush()

    user1 = User(
        email="alice@example.com", full_name="Alice Johnson", is_active=True
    )
    user2 = User(email="bob@example.com", full_name="Bob Smith", is_active=True)
    session.add_all([user1, user2])
    await session.flush()

    order1 = Order(user=user1, status="completed", total_amount=1199.98)
    order2 = Order(user=user2, status="pending", total_amount=29.99)
    session.add_all([order1, order2])
    await session.flush()

    session.add_all(
        [
            OrderItem(
                order=order1, product=products[0], quantity=1, price=999.99
            ),
            OrderItem(
                order=order1, product=products[1], quantity=1, price=199.99
            ),
            OrderItem(
                order=order2, product=products[2], quantity=1, price=29.99
            ),
        ]
    )
    await session.commit()
    print("Seeded demo data.")


async def seed_admin_user(session: AsyncSession) -> None:
    """Create a default superadmin if none exists."""
    result = await session.execute(select(AdminUser).limit(1))
    if result.scalars().first() is not None:
        return

    hashed = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
    admin_user = AdminUser(
        email="admin@example.com",
        hashed_password=hashed,
        full_name="Admin",
        is_superuser=True,
        is_active=True,
    )
    session.add(admin_user)
    await session.commit()
    print("Created default admin user: admin@example.com / admin")


# Lifespan context manager for FastAPI startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    print("Starting FastAPI Admin Example...")

    # Create all tables (user models + admin internals)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(AdminBase.metadata.create_all)
    print("Database tables ready.")

    # Seed demo data
    async with async_session_maker() as session:
        await seed_demo_data(session)
        await seed_admin_user(session)

    # Initialize admin
    await admin.setup(app)
    print("FastAPI Admin initialized successfully!")

    yield

    # Shutdown
    print("Shutting down...")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="FastAPI Admin Example",
    description="Demonstration of FastAPI Admin with multiple models",
    version="1.0.0",
    lifespan=lifespan,
)


# Initialize admin with customizations
admin = Admin(
    app=app,
    engine=engine,
    base=Base,
    title="My Admin Panel",
    logo_url=None,
    primary_color="#3b82f6",
    admin_path="/admin",
    dark_mode_default=False,
    per_page_default=25,
    secret_key=SECRET_KEY,
    auth_backend=BuiltinAuthBackend(),
)


# Register models with their admin classes
admin.register(Category, CategoryAdmin)
admin.register(Product, ProductAdmin)
admin.register(User, UserAdmin)
admin.register(Order, OrderAdmin)


# ============================================================================
# API Routes
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to FastAPI Admin Example!",
        "docs": "/docs",
        "admin": "/admin",
        "models": ["categories", "products", "users", "orders"],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# ============================================================================
# Run Instructions
# ============================================================================
# To run this example:
#   pip install -e .
#   python -m uvicorn example:app --reload
#
# Then visit:
#   Admin Panel: http://localhost:8000/admin
#   API Docs:   http://localhost:8000/docs
#   Health:     http://localhost:8000/health
#
# Default admin login:
#   Email:    admin@example.com
#   Password: admin


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
