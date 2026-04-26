# Deviations from `BACKEND_SPEC` (MVP)

The published LaunchedChit spec describes **magic-link email** auth and **HTTP-only session cookies** (`session_id`).

**This repository uses a deliberately different auth stack (Path B in `docs/MVP_IMPLEMENTATION_PLAN.md`):**

| Topic | Product spec | This codebase |
|--------|----------------|---------------|
| Login | `POST /auth/magic-link` + `GET /auth/callback` | `POST /api/v1/auth/request-otp` + `POST /api/v1/auth/verify-otp` |
| Session | Cookie `session_id` → `sessions` table | **JWT** from `verify-otp`, sent as `Authorization: Bearer` |
| Current user | `GET /me` (cookie) | `GET /api/v1/auth/me` (Bearer) |
| User id type | UUID | **Integer** (existing schema) |
| Logout / sessions | `POST /auth/logout` + `sessions` table | Client discards token (add `/logout` later if needed) |
| **Products API path** | Spec shows `/products/...` at app root | **`/api/v1/products/...`**

**Products and votes** otherwise follow the spec’s shapes (feed fields, composite vote key, 409 on duplicate upvote) apart from `id` being numeric in JSON, not a UUID string.

**OpenAPI** is served at `GET /openapi.json` (FastAPI default on the app root, not under `/api/v1`).

Converging to the full spec (magic link + sessions + UUID users) is a follow-up if the team agrees.
