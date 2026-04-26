# LaunchChit

A FastAPI + PostgreSQL backend for developers to publish apps, gather tester feedback, comments, and votes.

## Local setup

### Prerequisites

- **Python 3.10+** (see `.python-version` if you use `pyenv` / `uv python`)
- **[uv](https://docs.astral.sh/uv/)** for installing dependencies
- **PostgreSQL** (local or Docker) for the app database

### 1. Install dependencies

From the project root:

```bash
uv sync
```

To include dev tools (e.g. tests):

```bash
uv sync --extra dev
```

### 2. PostgreSQL

Create a database and a user the app can use. Example (adjust names/passwords):

```sql
CREATE USER launchchit WITH PASSWORD 'your-secure-password';
CREATE DATABASE launchchit OWNER launchchit;
```

Or use a single `postgres` superuser for local development only (not for production).

The app is configured for **async SQLAlchemy** with the **`asyncpg`** driver. The connection URL must use the `postgresql+asyncpg` scheme.

### 3. Environment variables

Copy the example env file and edit it:

```bash
cp .env.example .env
```

Set at least:

| Variable         | Description |
|------------------|------------|
| `DATABASE_URL`   | e.g. `postgresql+asyncpg://launchchit:your-secure-password@localhost:5432/launchchit` |
| `SECRET_KEY`     | A long random string (used for signing; change in production) |
| `ENVIRONMENT`    | e.g. `development` |

See `app/config/settings.py` once implemented for any extra options (CORS, feature flags, etc.).

### 4. Run the API

```bash
uv run uvicorn app.main:app --reload
```

The app will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000) (or the host/port you pass to Uvicorn). API docs, when routes exist, are typically at `/docs` (OpenAPI) and `/redoc`.

### 5. Database migrations (Alembic)

Schema changes are managed with **Alembic**. After SQLAlchemy models exist under `app/models/` and your Alembic layout is in place, follow the steps in **[`alembic/README.md`](alembic/README.md)** to create and apply migrations against your PostgreSQL database.

Until models and `alembic/` are fully configured, run creation commands from the project root as described there.

## Project layout

For a file-by-file overview, see [`docs/FILE_STRUCTURE.md`](docs/FILE_STRUCTURE.md).

## Tests

```bash
uv run pytest
```

(Requires `uv sync --extra dev`.)
