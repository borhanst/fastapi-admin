# FastAPI Admin

A drop-in admin panel for FastAPI + SQLAlchemy apps.

## Features

- Zero-config auto-discovery of SQLAlchemy models
- Built-in audit logging and RBAC
- Modern UI with Tailwind CSS, HTMX, and Alpine.js
- Fully customizable widgets and templates

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from fastapi_admin import Admin

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)

app = FastAPI()
admin = Admin(app, prefix="/admin")
admin.register(Product)
```

## Configuration

See `AGENT.md` for detailed configuration options and architecture.
