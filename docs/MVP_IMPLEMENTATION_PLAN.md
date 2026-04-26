# LaunchChit — MVP implementation plan

This document tracks progress on the MVP implementation.

## Auth model: Password-based signup + activation (COMPLETE ✓)

**As of 2026-04-26**, we have implemented **password-based signup/login** with email activation:

| Component | Implementation |
|-----------|---|
| Signup | `POST /api/v1/auth/signup` (username, email, password, confirm_password) → user created **inactive** |
| Activation | `GET /api/v1/auth/activate?email=...&token=...` → user becomes active; token valid 24h |
| Login | `POST /api/v1/auth/login` (email_or_username, password) → **JWT** in response |
| Me | `GET /api/v1/auth/me` + **Bearer** token → user info |
| User model | `id` (int), `username` (unique), `email` (unique), `password_hash`, `is_active`, `created_at` |
| Password hash | PBKDF2-SHA256, 100K iterations |
| Tests | 5 passing: signup → activate → login → `/me` flow |

**OTP / SMS (Integify) paused** — `otp_codes` table remains in schema but is **not used** in auth flow.

---

## MVP task checklist

### Phase 0 — Auth ✓
- [x] Password-based signup, activation, login
- [x] PBKDF2 hashing with salt
- [x] JWT token generation and Bearer auth
- [x] Input validation (username, email, password strength)
- [x] Tests for signup → activate → login → `/me`

### Phase 1 — Database ✓
- [x] User model refactored: `username`, `password_hash`, `is_active` (removed `phone`, `name`)
- [x] Alembic migration applied (recreates users table for SQLite compatibility)
- [x] Products table: `slug` (unique), `name`, `description`, `maker_id`, `vote_count`, `created_at`
- [x] Votes table: composite PK `(user_id, product_id)`
- [x] Indexes: slug, created_at, product_id on votes

### Phase 2 — Products & votes domain logic ✓
- [x] Slug service: lowercased, hyphenated, unique
- [x] Product service: create, today feed, by slug, vote tracking
- [x] Vote service: insert, delete, vote_count updates

### Phase 3 — Products API endpoints (PENDING)
- [ ] `GET /api/v1/products/today` (optional auth for `has_voted`)
- [ ] `GET /api/v1/products/{slug}`
- [ ] `POST /api/v1/products` (auth required)
- [ ] `POST /api/v1/products/{id}/vote` (auth required)
- [ ] `DELETE /api/v1/products/{id}/vote` (auth required)

### Phase 4 — Testing (PENDING)
- [ ] Products CRUD tests
- [ ] Vote uniqueness and vote_count consistency
- [ ] "Today" feed filtering (24h window)
- [ ] 404, 409 error cases
- [ ] Integration tests

### Phase 5 — OpenAPI & documentation (PENDING)
- [ ] Export OpenAPI schema for frontend
- [ ] Document API changes, env vars
- [ ] Update README with setup and auth flow

---

## Database schema (current)

| Table | Columns | Status | Notes |
|-------|---------|--------|-------|
| `users` | `id`, `username` (unique), `email` (unique), `password_hash`, `is_active`, `created_at` | ✓ Active | Password-based auth |
| `otp_codes` | `id`, `user_id`, `code`, `contact`, `expires_at`, `used`, `created_at` | ⏸ Paused | Exists; not used (SMS paused) |
| `products` | `id`, `slug` (unique), `name`, `tagline`, `description`, `website_url`, `logo_url`, `maker_id`, `vote_count`, `created_at` | ✓ Active | Awaiting API endpoints |
| `votes` | `user_id`, `product_id` (composite PK), `created_at` | ✓ Active | Awaiting API endpoints |

---

## Environment & required settings

**`.env` variables:**
```
DATABASE_URL=sqlite+aiosqlite:///./launchchit.db
JWT_SECRET_KEY=<random-long-string>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080  # 7 days

SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=<mailtrap-username>
SMTP_PASSWORD=<mailtrap-password>
SMTP_FROM=noreply@launchchit.com
```

**Paused (not used):**
- `SMS_API_KEY`, `SMS_EMAIL`, `SMS_PASSWORD` — kept in `.env.example` for future; not loaded in auth flow

---

## Next immediate steps

1. **Implement product endpoints** (Phase 3)
   - Reuse existing `Product`, `Vote` models
   - Wire routers in `app/api/v1/products.py`
   - Call service methods from endpoints

2. **Write product tests** (Phase 4)
   - Test create, get today, get by slug, vote/unvote
   - Verify vote_count consistency
   - Check auth and error cases

3. **Export OpenAPI schema** (Phase 5)
   - Verify `GET /openapi.json` includes product endpoints
   - Share with frontend team

---

## Key decisions

- **Auth:** Password-based with email activation (not magic link, not cookies)
- **User ID:** Integer (not UUID) — easier for now, can migrate later
- **Vote count:** Stored on products table, updated in app (not trigger-based yet)
- **OTP/SMS:** Paused; table remains for future use without schema loss

*Last updated: 2026-04-26 — Auth complete and tested. Products/votes ready for Phase 3 API endpoints.*
