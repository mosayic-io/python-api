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
│   │   └── auth_router.py     # Auth endpoints
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

- **API**: Deployed to Google Cloud Run (see `.github/workflows/gcp-deploy.yaml`)
- **Database**: Migrations deployed via GitHub Actions (see `.github/workflows/supabase-deploy-migrations.yaml`)

The command to deploy is:

```bash
# Set the variables
export PROJECT_ID=
export REGION=us-east1
export SERVICE_NAME=

# Get the project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Give the deployment service account access to the secrets
gcloud projects add-iam-policy-binding $PROJECT_NUMBER \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --project=$PROJECT_ID \
  --allow-unauthenticated \
  --service-account="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
```
