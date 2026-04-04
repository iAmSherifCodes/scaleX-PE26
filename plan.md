# URL Shortener — Implementation Plan

## Goal
Build a scalable URL shortener on Flask + Peewee + PostgreSQL. Focus: fast redirects, async event logging, proper DB indexes, paginated list endpoints, and basic API key auth.

---

## Phase 1: Models

### `app/models/user.py`
Fields: `id`, `username`, `email`, `api_key` (unique — for auth), `created_at`

### `app/models/url.py`
Fields: `id`, `user_id` (FK → User), `short_code` (6 chars, unique), `original_url`, `title`, `is_active` (default True), `created_at`, `updated_at`

### `app/models/event.py`
Fields: `id`, `url_id` (FK → Url), `user_id` (FK → User), `event_type` (`created` | `updated` | `deleted` | `clicked`), `timestamp`, `details` (raw JSON string)

**Register all three in `app/models/__init__.py`**

---

## Phase 2: DB Indexes (scalability baseline)

Defined on model `Meta` classes:
- `Url.short_code` — unique index (every redirect hits this)
- `Url.user_id` — index (list user's URLs)
- `Event.url_id` — index (event history per URL)
- `Event.user_id` — index (activity per user)
- `Event.event_type` — index (filter clicks for analytics)

---

## Phase 3: Seed Script (`seed.py` at project root)

```
uv run seed.py
```

- Load order: users → urls → events (FK dependency order)
- Uses `db.atomic()` + `chunked(..., 100)` for bulk inserts
- Parses datetime strings for `created_at`, `updated_at`, `timestamp`
- Stores `details` as raw JSON string (no parsing)
- Creates tables before inserting: `db.create_tables([User, Url, Event])`
- CSV paths: `../users.csv`, `../urls.csv`, `../events.csv`

---

## Phase 4: Auth (`app/auth.py`)

Simple API key via `X-API-Key` request header.

- `require_auth` decorator: reads header → looks up user → injects `g.current_user` → 401 if invalid
- `assert_owner(url, user)` helper → 403 if `url.user_id != user.id`

*Seeded users won't have api_keys — seed script generates and prints one per user, or a `POST /api/auth/token` endpoint issues keys.*

---

## Phase 5: Short Code Generation (`app/utils.py`)

- `generate_short_code()` → 6-char mixed-case alphanumeric using `secrets.choice`
- Retry loop on collision

---

## Phase 6: Async Event Logging (`app/events.py`)

- `log_event(url_id, user_id, event_type, details: dict)` serializes details to JSON and fires a daemon thread
- Thread opens its own DB connection (Peewee thread-safety requirement)
- Used for `clicked` events only — `created/updated/deleted` are logged synchronously in the request

---

## Phase 7: Routes

### `app/routes/redirect.py` — no URL prefix
| Method | Path | Description |
|--------|------|-------------|
| GET | `/<short_code>` | Lookup by short_code WHERE is_active=True → 302 redirect; async log `clicked` event; 404 if not found |

### `app/routes/urls.py` — prefix `/api/urls`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | yes | Create URL; generate short_code; log `created` event |
| GET | `/<id>` | no | Get URL detail |
| PATCH | `/<id>` | yes, owner | Update title/original_url/is_active; log `updated` event |
| DELETE | `/<id>` | yes, owner | Soft delete (is_active=False); log `deleted` event |

### `app/routes/users.py` — prefix `/api/users`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/<id>/urls` | Paginated list of user's URLs (`?page=1&per_page=20`) |
| GET | `/<id>/events` | Paginated list of user's events |

### `app/routes/events.py` — prefix `/api/urls`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/<id>/events` | Paginated event history for a URL, ordered by timestamp desc |

**Register all blueprints in `app/routes/__init__.py`**

---

## File Touch List

| File | Action |
|------|--------|
| `app/models/user.py` | Create |
| `app/models/url.py` | Create |
| `app/models/event.py` | Create |
| `app/models/__init__.py` | Edit |
| `app/auth.py` | Create |
| `app/utils.py` | Create |
| `app/events.py` | Create |
| `app/routes/redirect.py` | Create |
| `app/routes/urls.py` | Create |
| `app/routes/users.py` | Create |
| `app/routes/events.py` | Create |
| `app/routes/__init__.py` | Edit |
| `seed.py` | Create |
| `CLAUDE.md` | Create |

---

## Verification

```bash
uv sync
createdb hackathon_db
# configure .env
uv run seed.py              # 400 users, 2000 URLs, 3422 events
uv run run.py               # server starts on :5000

curl http://localhost:5000/health
# → {"status":"ok"}

curl -L http://localhost:5000/4mya84
# → 302 redirect to https://opswise.net/brisk/trail/1

curl http://localhost:5000/api/users/1/urls?page=1&per_page=5
# → paginated JSON

curl -X POST http://localhost:5000/api/urls \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com", "title": "Test"}'
# → 201 with short_code
```
