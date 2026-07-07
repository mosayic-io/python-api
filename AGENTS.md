# Agent Guidelines

This document provides essential context for AI agents working on this codebase.

## Overview

This is a **FastAPI** application with a **Supabase** (PostgreSQL) database backend. Testing uses **pytest**.

## Core Architecture

### Application Structure

```
app/
├── core/
│   ├── auth.py              # JWT verification dependency + auth helpers
│   ├── logger.py            # Colored console logger
│   ├── settings.py          # Environment variables via Pydantic
│   └── supabase_client.py   # Singleton async Supabase client
├── routes/
│   └── auth_router.py       # Auth endpoints (e.g. DELETE /auth/users/me)
├── tests/
│   ├── conftest.py          # Shared fixtures (app, async_client)
│   └── test_*.py            # Endpoint tests
├── __init__.py              # FastAPI app initialization with lifespan and CORS
└── main.py                  # API endpoints and route registration
```

**Key principles:**
- **Routes (`app/routes/`)**: One router file per feature, HTTP endpoint definitions only
- **Services (`app/services/`)**: Create this folder as the app grows — business logic and
  error handling for each feature live here, keeping routers thin
- **Core third-party services (`app/core/`)**: Class-based wrappers for external APIs
  (Supabase, Stripe, Cloudinary, etc.) with initialization and API key loading in `__init__`

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
- `supabase_secret_key` - Supabase secret (service role) key
- `environment` - Current environment (development/production). Interactive API docs are disabled in production.

Add new settings as typed fields on the `Settings` class; they load from `.env` or real environment variables automatically.

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
# app/routes/example_router.py
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

Third-party services (Supabase, Stripe, Cloudinary, etc.) are encapsulated in dedicated **class-based** modules within the `app/core/` directory. API key loading and client initialization happens in the `__init__` method. See `app/core/supabase_client.py` for the pattern in use.

```python
# app/core/stripe.py (example of adding a new integration)
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

### Authentication

Protect any endpoint by depending on `get_current_user`, which verifies the Supabase JWT
from the `Authorization: Bearer <token>` header:

```python
from fastapi import APIRouter, Depends
from supabase_auth.types import User

from app.core.auth import get_current_user

router = APIRouter()

@router.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    return {"user_id": user.id}
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

Tests live in `app/tests/`, one file per feature (`test_routes.py`, `test_auth_delete.py`, ...).

### Key Fixtures (see `app/tests/conftest.py`)

- `app` - Fresh FastAPI app instance with cleared dependency overrides
- `async_client` - HTTP client for endpoint testing

Override auth in tests with FastAPI dependency overrides:

```python
from types import SimpleNamespace
from app.core.auth import get_current_user
from app.main import app as fastapi_app

async def override_current_user():
    return SimpleNamespace(id="123")

fastapi_app.dependency_overrides[get_current_user] = override_current_user
```

## Database

### Supabase Configuration

- Local config: `supabase/config.toml`
- Migrations: `supabase/migrations/`

### Current Schema

**Tables:**
- `users` - User profiles (synced with Supabase Auth via triggers)
- `devices` - Push notification tokens, one row per device, foreign key to users

**Key features:**
- Row Level Security (RLS) enabled on all tables
- Automatic `updated_at` timestamps via triggers
- Auth triggers sync users from `auth.users` to `public.users` (and delete them in tandem)

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
| Install dependencies | `uv sync --all-groups` |
| Run dev server | `uv run uvicorn app.main:app --reload --port 8080` |
| Run tests | `uv run pytest` |
| Start local Supabase | `supabase start` |
| Push migrations | `supabase db push` |
| Build Docker | `docker build -t mosayic-api .` |
