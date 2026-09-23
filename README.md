# Python API

The backend for the React Native mobile app at Kealy Studio. It has two halves:

- **`supabase/`** — the database: schema, row-level security and the SQL
  functions that ship with it as migrations. Everything the app needs before
  its first store submission lives here — including account deletion, which
  the stores require and which runs as a Postgres function
  (`delete_own_account`) rather than on a server of your own.
- **`app/`** — the Python (FastAPI) API for everything beyond that: AI
  features, email, push, background work. It also carries account deletion
  as an endpoint (`DELETE /auth/users/me`) for apps that would rather route
  it through the server. Nothing in the fresh mobile app calls the API, so
  you can leave deploying it until a feature needs it.

## Tech Stack

- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Package Manager**: uv
- **Testing**: pytest, pytest-asyncio, pytest-mock
- **Deployment**: Docker, Google Cloud Run

## Project Structure

```
python-api/
├── app/
│   ├── core/
│   │   ├── auth.py            # JWT verification dependency + auth helpers
│   │   ├── logger.py          # Colored console logger
│   │   ├── settings.py        # Environment configuration (Pydantic)
│   │   └── supabase_client.py # Singleton async Supabase client
│   ├── routes/
│   │   └── email_router.py    # Welcome email (Supabase database webhook)
│   ├── services/
│   │   └── email.py           # Outgoing email via Resend (EMAIL_ENABLED gate)
│   ├── tests/
│   │   ├── conftest.py        # pytest fixtures
│   │   └── test_*.py          # Endpoint tests
│   ├── __init__.py            # FastAPI app initialization
│   └── main.py                # API endpoints and route registration
├── supabase/
│   ├── migrations/            # Database migrations (schema, RLS, delete_own_account, keepalive)
│   └── config.toml            # Local Supabase configuration
├── .github/workflows/         # CI/CD workflows
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Account deletion

Apple and Google require an in-app way to delete an account. It is a
database function, shipped by migration, so it exists in production the
moment your first release runs the migrations — no API deploy needed:

```ts
await supabase.rpc('delete_own_account')
```

`delete_own_account()` is `SECURITY DEFINER`, takes no arguments, deletes only
`auth.uid()` (the caller's own id from their session token), and may only be
executed by signed-in users. Deleting the `auth.users` row cascades to the
`public.users` row (the foreign key added in
`20260917200000_users_follow_auth_users.sql`), and on to `devices`. See the
migration `20260905120000_delete_own_account.sql` for the full reasoning.

The same deletion also exists as an API endpoint, `DELETE /auth/users/me`
(`app/routes/auth_router.py`): the server deletes the caller with the
service-role key. The mobile app ships both and one constant chooses —
`ACCOUNT_DELETION` in its `src/lib/api.ts`, `'database'` by default,
`'api'` to go through the server (which then has to be running, and deployed
before the store).

## Python API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Public | Welcome message |
| GET | `/protected` | Bearer JWT | Example authenticated route |
| POST | `/emails/welcome` | X-Webhook-Secret header | Send the welcome email — intended for a Supabase database webhook on `public.users` inserts (or, once email confirmation is on, a trigger on the moment `auth.users.email_confirmed_at` is set, so the welcome never beats the confirmation) |

Interactive docs are served at `/docs` (disabled when `APP_ENV=production`).

## Getting Started

### Prerequisites

- [Supabase CLI](https://supabase.com/docs/guides/cli) + Docker (the local database)
- Python 3.10 - 3.12 and [uv](https://github.com/astral-sh/uv) (the API)

### Installation

1. Copy environment variables:
   ```bash
   cp .env.example .env
   cp supabase/.env.example supabase/.env
   ```

2. Start local Supabase — database and auth:
   ```bash
   supabase start
   ```

That's everything the fresh app needs. The Python API, for when you add to it:

3. Install its dependencies:
   ```bash
   uv sync --all-groups
   ```

4. Run the development server:
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

### Running Tests

```bash
uv run pytest
```



## Database

Supabase migrations are in `supabase/migrations/`. Current schema includes:

- `users` - User profiles synced with Supabase Auth
- `devices` - A user may have many devices

### Keeping a free project awake

Supabase pauses a free-plan project after about a week without database
activity, and only a click in its dashboard brings it back. The migration
`20260910170000_keepalive.sql` adds `keepalive()`, a function that reads
nothing and returns the database's current time. Anything that pings on a
schedule can call it with just the publishable key:

```bash
curl https://<project-ref>.supabase.co/rest/v1/rpc/keepalive \
  -H "apikey: <your publishable key>"
```

It needs no API deploy. Send the key as the `apikey` header: the local stack
reads a `?apikey=` query parameter as a function argument.



## Deployment

Publishing a GitHub release is the single deploy ceremony — every workflow
runs on it:

- **Database**: migrations are pushed to production — this alone makes the app store-ready, account deletion included (see `.github/workflows/supabase-deploy-migrations.yaml`)
- **API**: the code is deployed to Google Cloud Run (see `.github/workflows/gcp-deploy.yaml`) — needed only once a feature calls it

A third workflow runs on its own clock rather than on releases: every night
`.github/workflows/scheduled-backups.yaml` dumps the production database into
a Google Cloud Storage bucket you own (the free Supabase tier keeps no backups
of its own). It reuses the deploy workflow's `github-deployer` key and the
migrations workflow's connection string, so set up automatic deploys first;
the bucket and two `env:` values are its one-time setup, documented in its
header.

The API workflow needs a one-time setup, documented in its own header: fill
in the `env:` block (service name, region, Supabase URL), then create a
`github-deployer` service account and hand its key to GitHub as the
`GCLOUD_SERVICE_KEY` secret. Until that's done, it skips itself quietly on
each release. Deploys run as the `github-deployer` account; the service
itself runs as the project's default compute service account, which needs
`roles/secretmanager.secretAccessor` to read its secret from Secret Manager.

To deploy by hand instead (the same command the workflow runs):

```bash
gcloud run deploy <appname>-api-service \
  --source . \
  --region=us-east1 \
  --allow-unauthenticated \
  --update-env-vars="APP_ENV=production,LOG_LEVEL=INFO,SUPABASE_URL=<your prod supabase url>" \
  --update-secrets="SUPABASE_SECRET_KEY=SUPABASE_SECRET_KEY:latest" \
  --clear-base-image
```
