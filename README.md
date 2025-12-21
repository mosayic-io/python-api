# Mosayic Python API

A FastAPI backend application with Supabase database integration.

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
   uv sync
   ```

2. Start local Supabase:
   ```bash
   supabase start
   ```

3. Copy environment variables:
   ```bash
   cp .env.local.example .env.local
   ```

4. Run the development server:
   ```bash
   uv run uvicorn app.main:app --reload --port 8080
   ```

### Running Tests

```bash
uv run pytest
```

### Docker

Build and run the container:

```bash
docker build -t mosayic-api .
docker run -p 8080:8080 mosayic-api
```

## Environment Variables

Configure in `.env.local` for development:

| Variable | Description |
|----------|-------------|
| `supabase_url` | Supabase project URL |
| `supabase_service_role_key` | Supabase service role key |
| `api_key` | API authentication key |
| `debug_mode` | Enable debug mode (default: false) |
| `environment` | Environment name (development/production) |

## Database

Supabase migrations are in `supabase/migrations/`. Current schema includes:

- `users` - User profiles synced with Supabase Auth
- `items` - User-owned items

Run migrations locally:
```bash
supabase db push
```

## Deployment

- **API**: Deployed to Google Cloud Run (see `.github/workflows/gcp-deploy.yaml`)
- **Database**: Migrations deployed via GitHub Actions (see `.github/workflows/supabase-deploy-migrations.yaml`)
