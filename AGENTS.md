# Agent Guidelines

This document provides essential context for AI agents working on this codebase.

## Overview

This is a **FastAPI** application with a **Supabase** (PostgreSQL) database backend. Testing uses **pytest**.

## Core Architecture

### Application Structure

```
app/
├── core/
│   ├── settings.py    # Environment variables via Pydantic
│   ├── supabase.py    # Supabase client class
│   ├── stripe.py      # Stripe client class
│   └── cloudinary.py  # Cloudinary client class (and other third-party services)
├── services/
│   ├── example_service.py   # Feature-specific business logic
│   └── (other services)     # Each feature gets its own service file
├── routers/
│   ├── example_router.py    # Feature-specific route definitions
│   └── (other routers)      # Each feature gets its own router file
├── __init__.py              # FastAPI app initialization with lifespan and CORS
└── main.py                  # Route registration
```

**Key principles:**
- **Services (`app/services/`)**: Business logic and error handling for each feature
- **Routers (`app/routers/`)**: HTTP endpoint definitions only
- **Core third-party services (`app/core/`)**: Class-based wrappers for external APIs (Supabase, Stripe, Cloudinary, etc.) with initialization and API key loading in `__init__`

### Environment Variables

Environment variables are managed through Pydantic settings in `app/core/settings.py`.

**How to access settings:**

```python
from app.core.settings import get_settings

settings = get_settings()

# Access variables
url = settings.supabase_url
key = settings.supabase_secret_key
```

The `get_settings()` function is cached with `@lru_cache()` to ensure a single instance is reused.

**Available settings:**
- `supabase_url` - Supabase project URL
- `supabase_secret_key` - Supabase service role key
- `api_key` - API authentication key
- `debug_mode` - Enable debug mode (bool)
- `environment` - Current environment (development/production)

## Code Standards

### Import Rules

**All imports must be at the top of each file.** Never place imports inside functions or classes.

```python
# CORRECT
from app.core.settings import get_settings
from fastapi import APIRouter, HTTPException

settings = get_settings()

def my_function():
    return settings.supabase_url

# INCORRECT - DO NOT DO THIS
def my_function():
    from app.core.settings import get_settings  # Never import inside functions
    settings = get_settings()
    return settings.supabase_url
```

### Router and Service Pattern

When creating new endpoints, follow the router/service separation:

1. **Router files** - Define routes, handle HTTP concerns only
2. **Service files** - Business logic and error handling

**Router file (handles routing only):**

```python
# app/routers/example_router.py
from fastapi import APIRouter, Depends
from app.services.example_service import ExampleService

router = APIRouter(prefix="/examples", tags=["examples"])

@router.get("/{example_id}")
async def get_example(example_id: str):
    service = ExampleService()
    return await service.get_by_id(example_id)
```

**Service file (handles logic and errors):**

```python
# app/services/example_service.py
from fastapi import HTTPException
from app.core.settings import get_settings

settings = get_settings()

class ExampleService:
    async def get_by_id(self, example_id: str):
        # Business logic here
        result = await self._fetch_from_db(example_id)

        # Error handling in service, NOT in router
        if not result:
            raise HTTPException(status_code=404, detail="Example not found")

        return result
```

### External Services (Third-Party Integrations)

Third-party services (Supabase, Stripe, Cloudinary, etc.) are encapsulated in dedicated **class-based** modules within the `app/core/` directory. API key loading and client initialization happens in the `__init__` method.

**Example structure:**

```python
# app/core/supabase.py
from supabase import create_client, Client
from app.core.settings import get_settings


class SupabaseClient:
    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_secret_key
        )

    def query(self, table: str):
        return self.client.table(table)
```

```python
# app/core/stripe.py
import stripe
from app.core.settings import get_settings


class StripeClient:
    def __init__(self):
        settings = get_settings()
        stripe.api_key = settings.stripe_secret_key
        self.stripe = stripe

    def create_checkout_session(self, **kwargs):
        return self.stripe.checkout.Session.create(**kwargs)
```

```python
# app/core/cloudinary.py
import cloudinary
from app.core.settings import get_settings


class CloudinaryClient:
    def __init__(self):
        settings = get_settings()
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret
        )

    def upload(self, file, **kwargs):
        return cloudinary.uploader.upload(file, **kwargs)
```

## Testing

### Framework

Tests use **pytest** with the following packages:
- `pytest` - Core testing framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking utilities

### Running Tests

```bash
uv run pytest
```

### Test Structure

```
tests/
├── fixtures/
│   ├── database_fixtures.py   # Supabase mocks
│   └── auth_fixtures.py       # Auth mocks
└── conftest.py                # Shared fixtures
```

### Key Fixtures

- `app` - Fresh FastAPI app instance
- `async_client` - HTTP client for endpoint testing
- `mock_supabase` - Mocked Supabase client with success responses
- `mock_supabase_error` - Mocked Supabase client with error responses

### Example Test

```python
import pytest

@pytest.mark.asyncio
async def test_get_example(async_client, mock_supabase):
    response = await async_client.get("/examples/123")
    assert response.status_code == 200
```

## Database

### Supabase Configuration

- Local config: `supabase/config.toml`
- Migrations: `supabase/migrations/`
- Project ID: `python-api`

### Current Schema

**Tables:**
- `users` - User profiles (synced with Supabase Auth)
- `items` - User-owned items with foreign key to users

**Key features:**
- Row Level Security (RLS) enabled on all tables
- Automatic `updated_at` timestamps via triggers
- Auth triggers sync users from `auth.users` to `public.users`

### Running Migrations

```bash
# Local
supabase db push

# View current status
supabase status
```

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Run dev server | `uv run uvicorn app.main:app --reload --port 8080` |
| Run tests | `uv run pytest` |
| Start local Supabase | `supabase start` |
| Push migrations | `supabase db push` |
| Build Docker | `docker build -t mosayic-api .` |
