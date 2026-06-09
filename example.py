"""Example usage of FastAPI Admin with multiple models and configurations."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.sql import func

from fastapi_admin import Admin, ModelAdmin

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
        String(20), default="pending"
    )  # pending, processing, completed, cancelled
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


class OrderAdmin(ModelAdmin):
    """Admin configuration for Order model."""

    list_display = ["id", "user", "order_date", "status", "total_amount"]
    list_filter = ["status", "order_date"]
    search_fields = ["user__email"]
    ordering = ["-order_date"]
    fields = ["user", "order_date", "status", "total_amount"]
    readonly_fields = ["order_date", "created_at"]
    verbose_name = "Order"
    verbose_name_plural = "Orders"


# ============================================================================
# FastAPI Application Setup
# ============================================================================

# Database configuration
DATABASE_URL = "sqlite+aiosqlite:///./example.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Lifespan context manager for FastAPI startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Starting FastAPI Admin Example...")
    # Note: Database tables are created via Alembic migrations
    # Just initialize admin
    await admin.setup(app)
    print("✅ FastAPI Admin initialized successfully!")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await engine.dispose()
    print("✅ Shutdown complete!")


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
    base=Base,  # Pass user's DeclarativeBase
    title="My Admin Panel",
    logo_url=None,
    primary_color="#3b82f6",
    admin_path="/admin",
    dark_mode_default=False,
    per_page_default=25,
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
#   API Docs: http://localhost:8000/docs
#   Health: http://localhost:8000/health


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
