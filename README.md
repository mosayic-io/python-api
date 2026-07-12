# Python API

A FastAPI backend application with Supabase database integration, designed to complement the React Native mobile application stack at Kealy Studio.

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
│   │   ├── auth_router.py     # Auth endpoints
│   │   └── email_router.py    # Welcome email (Supabase database webhook)
│   ├── services/
│   │   └── email.py           # Outgoing email via Resend (EMAIL_ENABLED gate)
│   ├── tests/
│   │   ├── conftest.py        # pytest fixtures
│   │   └── test_*.py          # Endpoint tests
│   ├── __init__.py            # FastAPI app initialization
│   └── main.py                # API endpoints and route registration
├── supabase/
│   ├── migrations/            # Database migrations
│   └── config.toml            # Local Supabase configuration
├── .github/workflows/         # CI/CD workflows
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Public | Welcome message |
| GET | `/protected` | Bearer JWT | Example authenticated route |
| DELETE | `/auth/users/me` | Bearer JWT | Delete the authenticated user's account |
| POST | `/emails/welcome` | X-Webhook-Secret header | Send the welcome email — intended for a Supabase database webhook on `public.users` inserts |

Interactive docs are served at `/docs` (disabled when `APP_ENV=production`).

## Getting Started

### Prerequisites

- Python 3.10 - 3.12
- [uv](https://github.com/astral-sh/uv) package manager
- [Supabase CLI](https://supabase.com/docs/guides/cli) (for local development)

### Installation

1. Install dependencies:
   ```bash
   uv sync --all-groups
   ```

2. Start local Supabase:
   ```bash
   supabase start
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   cp supabase/.env.example supabase/.env
   ```

4. Run the development server:
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

### Running Tests

```bash
uv run pytest
```



## Database

Supabase migrations are in `supabase/migrations/`. Current schema includes:

- `users` - User profiles synced with Supabase Auth
- `devices` - A user may have many devices



## Deployment

Publishing a GitHub release is the single deploy ceremony — both workflows
run on it:

- **Database**: migrations are pushed to production first (see `.github/workflows/supabase-deploy-migrations.yaml`)
- **API**: the code is deployed to Google Cloud Run alongside (see `.github/workflows/gcp-deploy.yaml`)

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
  --update-secrets="SUPABASE_SECRET_KEY=SUPABASE_SECRET_KEY:latest"
```
