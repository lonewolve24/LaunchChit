# Migrations (Alembic)

When `app/models` contains SQLAlchemy metadata, run `alembic init alembic` from the project root (or add the generated `alembic/` folder here) and configure `alembic/env.py` to use your async engine and `Base.metadata` for autogenerate. Revision files live in `alembic/versions/`.
