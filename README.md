# Python API

A FastAPI backend application with Supabase database integration, designed to compliment the React Native Mobile application Stack at Kealy Studio.

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
│   │   ├── __init__.py
│   │   └── settings.py       # Environment configuration (Pydantic)
│   ├── __init__.py           # FastAPI app initialization
│   └── main.py               # API endpoints
├── supabase/
│   ├── migrations/           # Database migrations
│   └── config.toml           # Local Supabase configuration
├── tests/
│   ├── fixtures/             # Test fixtures
│   └── conftest.py           # pytest configuration
├── .github/workflows/        # CI/CD workflows
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

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
   mv .env.example .env
   mv supabase/.env.example supabase/.env
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
```
# Set the variables
export PROJECT_ID=goat-together
export REGION=eu-west1
export SERVICE_NAME=goattogether-api

# Get the project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --project=$PROJECT_ID \
  --allow-unauthenticated
```
