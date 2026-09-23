# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

The backend for the mobile app, in two halves:

- **`supabase/`** — the PostgreSQL database: schema, RLS and SQL functions,
  shipped as migrations. Account deletion (an app-store requirement) is a
  Postgres function here, `delete_own_account()`, so the app is store-ready
  before any server is deployed. The API ALSO ships it as an endpoint
  (`DELETE /auth/users/me`, `app/routes/auth_router.py`); the mobile app's
  `ACCOUNT_DELETION` constant (`src/lib/api.ts`) picks one — the database
  function by default.
- **`app/`** — the **FastAPI** application for everything beyond the
  database: AI features, email, push, background work. Nothing in the fresh
  mobile app calls it. Testing uses **pytest**.

## Production is not a place you run things

This repo has a development copy (the Supabase that `supabase start` runs in
Docker, and `uvicorn` on this machine) and a production deployment (the hosted
Supabase project and Cloud Run). You may READ production in a limited sense —
check whether an environment variable or secret exists, read a deployment's
status or logs — and you may SET a secret when the user explicitly asks you to.
You must NEVER run scripts, one-off commands, REPLs or SQL against the
production database or the deployed API: no `psql`, no SQL editor, no secret
key used from a dev machine, no `supabase db push`, no "just a quick SELECT".
Schema changes reach production one way only — as migration files shipped by a
release (see Shipping). If a task seems to need production data or a
production query, stop and ask.

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
│   ├── auth_router.py       # DELETE /auth/users/me — account deletion through the server (the app's second way; the database function is its default)
│   └── email_router.py      # POST /emails/welcome (Supabase database webhook)
├── services/
│   └── email.py             # Outgoing email via Resend — send_email(), EMAIL_ENABLED gate
├── tests/
│   ├── conftest.py          # Shared fixtures (app, async_client)
│   └── test_*.py            # Endpoint tests
├── __init__.py              # FastAPI app initialization with lifespan and CORS
└── main.py                  # API endpoints and route registration
```

**Key principles:**
- **Routes (`app/routes/`)**: One router file per feature, HTTP endpoint definitions only
- **Services (`app/services/`)**: Business logic and error handling for each feature live
  here, keeping routers thin — `email.py` (outgoing email via Resend, best-effort, gated
  by `EMAIL_ENABLED`) is the pattern to follow
- **Core third-party services (`app/core/`)**: Class-based wrappers for external APIs
  (Supabase, Cloudinary, etc.) with initialization and API key loading in `__init__`

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
- `app_env` - Current environment (development/production), set via `APP_ENV`. Interactive API docs are disabled in production.

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

Third-party services (Supabase, Cloudinary, etc.) are encapsulated in dedicated **class-based** modules within the `app/core/` directory. API key loading and client initialization happens in the `__init__` method. See `app/core/supabase_client.py` for the pattern in use.

```python
# app/core/cloudinary_client.py (example of adding a new integration)
import cloudinary
from app.core.settings import get_settings


class CloudinaryClient:
    def __init__(self):
        settings = get_settings()
        cloudinary.config(cloud_name=settings.cloudinary_cloud_name,
                          api_key=settings.cloudinary_api_key,
                          api_secret=settings.cloudinary_api_secret)
```

### Payments

Payments are **RevenueCat-first**: the mobile app talks to RevenueCat directly, and
RevenueCat holds subscription state — nothing here mirrors it. Stripe, when needed,
is wired through RevenueCat. This template ships no payment code; add server-side
pieces (e.g. a RevenueCat webhook) only when a feature needs them.

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

Tests live in `app/tests/`, one file per feature (`test_routes.py`, `test_emails.py`, ...).

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
- Auth emails: `supabase/templates/confirmation.html` and `recovery.html`,
  wired in `config.toml` under `[auth.email.template.*]`. Put the app's name
  in each header. **Email confirmation ships OFF** (`enable_confirmations =
  false`); the mobile app is already built for ON (its verify-email screen,
  the links site's `/email-confirmed` page), so switching it on is the
  config flag locally plus the hosted project's "Confirm email" toggle —
  keep the two in agreement. Locally, Mailpit at http://127.0.0.1:54324
  catches every auth email. The hosted project's templates are set under
  Authentication → Email Templates (Mosayic's email card does it for you).

### Current Schema

**Tables:**
- `users` - User profiles (synced with Supabase Auth via triggers)
- `devices` - Push notification tokens, one row per device, foreign key to users

**Key features:**
- Row Level Security (RLS) enabled on all tables
- Automatic `updated_at` timestamps via triggers
- Auth triggers sync users from `auth.users` to `public.users` (and delete them in tandem)
- `delete_own_account()` — `SECURITY DEFINER`, no arguments, deletes only
  `auth.uid()`, EXECUTE granted to `authenticated` only. The app calls it with
  `supabase.rpc('delete_own_account')` — or, with `ACCOUNT_DELETION = 'api'`
  in its `src/lib/api.ts`, `DELETE /auth/users/me` on this API, which does the
  same deletion with the service-role key. Follow the same shape for any future
  privileged-but-self-scoped operation; never accept a user id as a parameter.
- `keepalive()` — `STABLE`, `SECURITY INVOKER`, no arguments, reads no table,
  returns `now()`; EXECUTE granted to `anon` + `authenticated`. It's the
  harmless query a scheduled ping calls (`GET /rest/v1/rpc/keepalive` with the
  `apikey` header) so Supabase never pauses a free project for inactivity.
  Keep it table-free: it's open to anyone holding the public key.

### Migrations — the rules

Every database change — a table, a column, a policy, a SQL function, a storage
bucket — is a migration file in `supabase/migrations/`. Nothing is ever clicked
together in a dashboard.

- **One NEW file per change. Never edit, rename or delete an existing
  migration**: it has already run, here and possibly in production.
- **Name it `<UTC timestamp>_<what>.sql` with a timestamp LATER than every file
  already there**, e.g. `20260908143000_add_notes.sql`. A stamp that sorts
  before an existing file runs first and takes the whole chain down.
- Write plain Postgres the way the Supabase CLI applies it — no `psql`
  meta-commands. Every new table gets RLS enabled and its policies in the same
  file. Use `if not exists` / `on conflict do nothing` where a re-run is
  plausible.
- Privileged-but-self-scoped operations follow `delete_own_account()`:
  `SECURITY DEFINER`, no arguments, acts only on `auth.uid()`, EXECUTE granted
  to `authenticated` only. Never accept a user id as a parameter.

### Supabase Storage is part of the schema

A bucket is created in a migration, never in the dashboard: an INSERT into
`storage.buckets` (columns: `id`, `name`, `public`, `file_size_limit`,
`allowed_mime_types`; `on conflict (id) do nothing`) plus RLS policies on
`storage.objects`. Convention: every file lives at a path whose first folder is
the uploader's user id — `(storage.foldername(name))[1] = auth.uid()::text` —
and signed-in users may insert / update / delete only inside their own folder
of that bucket (`bucket_id = '…'` on every policy, and a policy name that
includes the bucket so features never clash). Public buckets (avatars) get an
anyone-can-select policy; private ones are read through signed URLs.

**The storage schema belongs to Supabase.** Never `ALTER` a table in it, never
`create` anything in it besides bucket rows and policies, and never `enable row
level security` on `storage.objects` — it already is, and a hosted project
refuses all of that with "must be owner". A migration that works locally and
dies on the first release is the one failure to design out.

`delete_own_account()` removes the user's rows but NOT their files in Storage —
a feature that adds a bucket should extend it (its migration says where).

### Applying migrations locally

```bash
npx supabase migration up   # only the files the local database hasn't seen — keeps your test data
npx supabase db reset       # everything from empty (seed.sql included) — the full proof
npx supabase status         # what's running, and the local keys
```

Then regenerate the mobile app's types from the live schema, from this folder:

```bash
npx supabase gen types typescript --local > ../<app>-mobile/src/types/database.ts
```

`supabase db push` is NOT for local work — it pushes to a *linked remote*
project, i.e. production, and is exactly the thing the rule above forbids.

## Shipping — a release is the deploy

`.github/workflows/` holds three workflows. Two run `on: release: published`:

- `supabase-deploy-migrations.yaml` applies every unapplied migration to the
  production database (needs the `DATABASE_CONNECTION_STRING` repository secret).
- `gcp-deploy.yaml` builds the container and deploys it to Cloud Run (needs
  `GCLOUD_SERVICE_KEY`; the `--update-secrets` line in it is where a production
  secret gets mounted from Secret Manager).

The third, `scheduled-backups.yaml`, runs on a nightly cron (03:27 UTC) and
dumps the production database — roles, schema, data — into a date-stamped
folder of a Google Cloud Storage bucket, daily/weekly/monthly tiers pruned by
a lifecycle rule on the bucket. It needs NO new secret: it reads the same
`DATABASE_CONNECTION_STRING` and uploads as the same `github-deployer` account
(`GCLOUD_SERVICE_KEY`, whose `roles/storage.admin` covers the bucket) — so
automatic deploys are set up first, then backups. The bucket, its retention
rule and the two values in the workflow's `env:` block are the one-time setup
(header comment; Mosayic's "Back up your database" card does it in one click).
Supabase's free tier keeps no backups, so this is the only copy; on Supabase
Pro it is redundant and can be disabled from the Actions tab. GitHub disables
scheduled workflows after 60 days without a push — re-enable from the same tab.

All three self-skip, green, until their secrets exist — a green run is not proof
of a deploy or a backup. Publishing a GitHub release (`gh release create v0.1.0`,
`v0.1.0` and `0.1.0` both fine) is the whole deploy ceremony; there is no other
path to production.

## Secrets

- `.env` is gitignored; `.env.example` is committed with every key blank. A new
  secret is a typed field on `Settings`, a real value in `.env`, a blank line in
  `.env.example`, and — for production — the same name in the project's Secret
  Manager plus the `--update-secrets` line in `gcp-deploy.yaml`. Never
  `os.environ` directly, never a key in a commit.
- Third-party API keys (AI providers, email, payments) live HERE, never in the
  mobile app: the phone calls this API, this API calls the provider.
- Dependencies are managed with **uv**: `uv add <package>` (with the extra, e.g.
  `uv add "pydantic-ai-slim[openai]"`), never `pip`, never editing `uv.lock` by
  hand.

## Before you call a change done

- `uv run pytest` passes — write a test for every endpoint you add, with any
  external call stubbed (pydantic-ai's `TestModel`, a mocked client) so the
  suite never hits the network or spends money.
- A new migration applies with `npx supabase migration up` and the app's
  `database.ts` is regenerated.

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync --all-groups` |
| Run dev server | `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080` |
| Run tests | `uv run pytest` |
| Start local Supabase | `npx supabase start` |
| Apply new migrations locally | `npx supabase migration up` |
| Rebuild the local database from empty | `npx supabase db reset` |
| Regenerate the app's types | `npx supabase gen types typescript --local > ../<app>-mobile/src/types/database.ts` |
| Ship to production | `gh release create v0.1.0` |
| Build the container locally | `docker build -t api .` |
