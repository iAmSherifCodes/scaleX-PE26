# Silver Tier Runbook

This runbook targets the Silver requirement:
- 200 concurrent users
- 2+ app instances behind Nginx load balancer
- p95 response time under 3 seconds
- Error rate under 5%

## 1) Start the scaled stack

```bash
docker compose -f docker-compose.silver.yml up -d --build
```

Verify containers (for screenshot proof):

```bash
docker ps
```

Expected: `app1`, `app2`, `app3`, `nginx`, `postgres` — all `Up`.

## 2) Seed data

From your host (local env pointing at `localhost:5432`), run:

```bash
uv sync
uv run seed.py
```

If you already seeded for Bronze, skip this step.

If the CSV files are unavailable, bootstrap a minimal test record:

```bash
docker compose -f docker-compose.silver.yml exec -T app1 uv run python - <<'PY'
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
            'username': 'silver_tester',
            'email': 'silver@example.com',
            'api_key': 'SILVER_TEST_API_KEY_1234567890',
            'created_at': datetime.utcnow(),
        },
    )
    Url.get_or_create(
        short_code='4mya84',
        defaults={
            'user_id': user.id,
            'original_url': 'https://example.com',
            'title': 'Silver Test URL',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        },
    )
print('ready: short_code=4mya84')
PY
```

## 3) Verify the load balancer is up

```bash
curl http://localhost:8080/health
# → {"status":"ok"}

curl -I http://localhost:8080/4mya84
# → HTTP/1.1 302 FOUND
```

## 4) How traffic is distributed

Nginx uses `least_conn` load balancing — each new request goes to the container with the fewest active connections:

```
Client → Nginx :8080
              ├── app1:5000  (Gunicorn: 4 workers × 8 threads)
              ├── app2:5000  (Gunicorn: 4 workers × 8 threads)
              └── app3:5000  (Gunicorn: 4 workers × 8 threads)
```

Total capacity: 3 containers × 32 concurrent requests = 96 concurrent requests.

## 5) Run the Silver scale-out test (200 VUs)

```bash
docker run --rm --network host \
  -e BASE_URL=http://localhost:8080 \
  -e HOT_PATH=/4mya84 \
  -v "$PWD/loadtest/k6:/scripts" \
  grafana/k6 run /scripts/silver.js
```

What this test does:
- Ramps 0 → 50 VUs over 15s
- Ramps 50 → 200 VUs over 15s
- Holds at 200 VUs for 60s
- Ramps down to 0 over 10s
- 80% of traffic hits the redirect path (`HOT_PATH`), 20% hits `/health`
- Enforces `http_req_failed < 5%`
- Enforces `p(95) < 3000ms`

## 6) Record verification artifacts

- Terminal screenshot of k6 output showing thresholds pass/fail
- `docker ps` screenshot showing `app1`, `app2`, `app3`, `nginx`, `postgres`
- p95 latency from k6 output (`http_req_duration p(95)`)
- Error rate from k6 output (`http_req_failed`)

## 7) Tear down

```bash
docker compose -f docker-compose.silver.yml down
```
