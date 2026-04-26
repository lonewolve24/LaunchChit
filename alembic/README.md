# Migrations (Alembic) + PostgreSQL

This project uses **PostgreSQL** and **SQLAlchemy** (async) with the **`asyncpg`** driver. Alembic handles schema changes over time.

## Before you use Alembic

1. **Models** – Define tables in `app/models/` and a shared `Base` / `metadata` that reflects your real schema.
2. **Config** – Ensure an Alembic layout exists (e.g. `alembic.ini` at the repo root and an `alembic/` package). If you are starting from this template’s empty `alembic/` folder, run from the project root:

   ```bash
   uv run alembic init alembic
   ```

   If that would overwrite this README, use a new directory name or back up this file first, then point `alembic.ini` at your `alembic/` folder. Adjust `env.py` so it:
   - loads the same `DATABASE_URL` as the app (from `.env` / `app.config.settings` once wired),
   - uses **`target_metadata = Base.metadata`** (import your `Base` from `app.models`) for autogenerate.

3. **URL for Alembic** – The runtime app uses `postgresql+asyncpg://...`. Alembic’s CLI often uses a **synchronous** URL for `env.py` (e.g. `postgresql+psycopg2://...` or `postgresql://...` with a sync driver), or you use Alembic’s [async support](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic) with the async engine. Pick one approach and keep it consistent with your `env.py` implementation.

## Typical workflow (once `env.py` is correct)

| Step | Command |
|------|--------|
| Autogenerate a revision from model changes | `uv run alembic revision --autogenerate -m "describe change"` |
| Create an empty migration | `uv run alembic revision -m "describe change"` |
| Apply migrations (upgrade) | `uv run alembic upgrade head` |
| Roll back one step | `uv run alembic downgrade -1` |
| See current DB revision | `uv run alembic current` |

Revision scripts live in **`alembic/versions/`** after the first generation.

## Local database

The database must already exist in PostgreSQL (see the main [README.md](../README.md#2-postgresql)). Alembic does not create the server or the empty database; it only applies your migration scripts to the database you point it at.
