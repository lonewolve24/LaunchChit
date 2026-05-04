# Developer Setup Guide

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url>
cd LaunchChit

# 2. Install dependencies
uv sync

# 3. Set up database
alembic upgrade head

# 4. Run tests
uv run pytest tests/ -v

# 5. Start server
uv run uvicorn app.main:app --reload
```

## Prerequisites

- **Python 3.11+** (or use `uv` which manages Python automatically)
- **uv** package manager ([install here](https://docs.astral.sh/uv/getting-started/installation/))

## Setup Steps

### 1. Install Dependencies

```bash
uv sync
```

This installs:
- All production dependencies (FastAPI, SQLAlchemy, etc.)
- All dev dependencies (pytest, pytest-asyncio) via `[dependency-groups] dev`
- Uses `uv.lock` for reproducible builds across all developers

### 2. Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your values. Key variables:
- `JWT_SECRET_KEY` - Secret key for JWT signing (generate a strong one!)
- `DATABASE_URL` - SQLite or Postgres connection string
- `SMTP_*` - Email configuration

### 3. Database Setup

Initialize the database:

```bash
alembic upgrade head
```

This creates all tables defined in the models.

### 4. Run Tests

All tests use an in-memory SQLite database (isolated):

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_products_complete.py -v

# With coverage
uv run pytest tests/ --cov=app
```

**Test Configuration**: See `conftest.py` - automatically loads `.env` and provides safe defaults.

### 5. Start Development Server

```bash
uv run uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs` (Swagger UI)
- Health check: `GET /api/v1/health`

## Project Structure

```
LaunchChit/
├── app/
│   ├── api/              # API routes
│   │   └── v1/           # v1 endpoints
│   ├── config/           # Settings, database config
│   ├── core/             # Security, password hashing
│   ├── models/           # SQLAlchemy models (User, Product, Vote)
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI app
├── tests/                # Pytest tests
├── alembic_migrations/   # Database migrations
├── conftest.py           # Pytest configuration
├── pyproject.toml        # Dependencies & metadata
└── uv.lock              # Locked dependency versions (DO NOT EDIT)
```

## Key Features Implemented

### Authentication
- **Signup**: `POST /api/v1/auth/signup` - Register new user
- **Activate**: `GET /api/v1/auth/activate?email=X&token=Y` - Activate account
- **Login**: `POST /api/v1/auth/login` - Get JWT token
- **Me**: `GET /api/v1/auth/me` - Get current user (requires Bearer token)

### Products
- **Create**: `POST /api/v1/products` - Create new product (requires auth)
- **Today Feed**: `GET /api/v1/products/today` - List products from today
- **By Slug**: `GET /api/v1/products/{slug}` - Get product detail
- **Vote**: `POST /api/v1/products/{product_id}/vote` - Vote for product
- **Unvote**: `DELETE /api/v1/products/{product_id}/vote` - Remove vote

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'python-jose'`

**Solution**: Run `uv sync` - ensures all dependencies are installed with correct Python version.

### Issue: Tests fail with version mismatch

**Solution**: Use `uv run pytest` instead of system pytest - ensures correct Python/package combo.

### Issue: Database is locked

**Solution**: Delete and recreate:
```bash
rm launchchit.db
alembic upgrade head
```

### Issue: Env variables not loading

**Solution**: `conftest.py` loads `.env` automatically. If not working:
```bash
# Verify .env exists and has required vars
cat .env

# Run with explicit env
JWT_SECRET_KEY=your-key uv run pytest tests/
```

## Architecture Notes

- **Async-first**: All database operations use async (SQLAlchemy async + aiosqlite)
- **Dependency injection**: FastAPI `Depends()` for database sessions
- **In-memory tokens**: Activation tokens stored in-memory (dev/test only, use persistence in production)
- **PBKDF2-SHA256**: Password hashing algorithm (standard library, no external deps)

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test: `uv run pytest tests/ -v`
3. Commit: `git commit -m "descriptive message"`
4. Push: `git push origin feature/my-feature`
5. Create pull request

## Testing

Tests are comprehensive:
- `tests/test_auth_signup_login.py` - Authentication flow
- `tests/test_products_complete.py` - Product CRUD and voting

Run with verbose output:
```bash
uv run pytest tests/ -v --tb=short
```

## Troubleshooting

### Clean slate (start fresh)
```bash
rm -rf .venv .pytest_cache uv.lock
uv sync
alembic downgrade base
alembic upgrade head
uv run pytest tests/ -v
```

### Check Python version used by uv
```bash
uv python list
uv show python
```

### Force specific Python version
```bash
uv sync --python 3.11
```

## Support

For issues, check:
1. `docs/MVP_IMPLEMENTATION_PLAN.md` - Project roadmap
2. `docs/SPEC_DEVIATIONS.md` - Known issues/changes from spec
3. `docs/TEST_ENVIRONMENT_SETUP.md` - Detailed test config

---

**Last Updated**: April 26, 2026
