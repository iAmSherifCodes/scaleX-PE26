# Bronze Tier Runbook

This runbook targets the Bronze requirement:
- 50 concurrent users
- Documented baseline p95 response time
- Documented error rate

## 1) Start the stack

```bash
docker compose -f docker-compose.bronze.yml up -d --build
```

Verify containers (for screenshot proof):

```bash
docker ps
```

Expected: 1 `app` container, 1 `postgres` container.

## 2) Seed data

From your host (local env pointing at `localhost:5432`), run:

```bash
uv sync
uv run seed.py
```

If the CSV files are unavailable, bootstrap a minimal test record:

```bash
docker compose -f docker-compose.bronze.yml exec -T app uv run python - <<'PY'
from datetime import datetime
from app import create_app
from app.database import db
from app.models.user import User
from app.models.url import Url
from app.models.event import Event

app = create_app()
with app.app_context():
    db.create_tables([User, Url, Event], safe=True)
    user, _ = User.get_or_create(
        id=1,
        defaults={
            'username': 'bronze_tester',
            'email': 'bronze@example.com',
            'api_key': 'BRONZE_TEST_API_KEY_1234567890',
            'created_at': datetime.utcnow(),
        },
    )
    Url.get_or_create(
        short_code='4mya84',
        defaults={
            'user_id': user.id,
            'original_url': 'https://example.com',
            'title': 'Bronze Test URL',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        },
    )
print('ready: short_code=4mya84')
PY
```

## 3) Verify the app is up

```bash
curl http://localhost:5000/health
# → {"status":"ok"}

curl -I http://localhost:5000/4mya84
# → HTTP/1.1 302 FOUND
```

## 4) Run the Bronze baseline test (50 VUs)

```bash
docker run --rm --network host \
  -e BASE_URL=http://localhost:5000 \
  -e HOT_PATH=/4mya84 \
  -v "$PWD/loadtest/k6:/scripts" \
  grafana/k6 run /scripts/bronze.js
```

What this test does:
- Ramps 0 → 10 VUs over 15s
- Ramps 10 → 50 VUs over 15s
- Holds at 50 VUs for 60s
- Ramps down to 0 over 10s
- 80% of traffic hits the redirect path (`HOT_PATH`), 20% hits `/health`
- Enforces `http_req_failed < 10%`
- Enforces `p(95) < 5000ms`

## 5) Record verification artifacts

- Terminal screenshot of k6 output showing thresholds pass/fail
- `docker ps` screenshot showing `app` and `postgres`
- p95 latency from k6 output (`http_req_duration p(95)`)
- Error rate from k6 output (`http_req_failed`)

## 6) Tear down

```bash
docker compose -f docker-compose.bronze.yml down
```
