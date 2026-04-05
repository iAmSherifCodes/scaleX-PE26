# Gold Tier Scalability Runbook

This runbook targets the Gold requirement:
- 100 req/sec (mission-allowed alternative to 500+ concurrent users)
- error rate under 5%
- Redis cache evidence
- bottleneck report

## 1) Start the scaled stack

```bash
docker compose -f docker-compose.gold.yml up -d --build
```

Verify containers (for screenshot proof):

```bash
docker ps
```

Expected: 3 app containers (`app1`, `app2`, `app3`), 1 `nginx`, 1 `redis`, 1 `postgres`.

## 2) Seed data

From your host (using local env pointing at localhost PostgreSQL), run:

```bash
uv sync
uv run seed.py
```

If you already seeded before, skip this step.

If the CSV files are unavailable, bootstrap a minimal test record:

```bash
docker compose -f docker-compose.gold.yml exec -T app1 uv run python - <<'PY'
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
			'username': 'gold_tester',
			'email': 'gold@example.com',
			'api_key': 'GOLD_TEST_API_KEY_1234567890',
			'created_at': datetime.utcnow(),
		},
	)
	Url.get_or_create(
		short_code='abc123',
		defaults={
			'user_id': user.id,
			'original_url': 'https://example.com',
			'title': 'Gold Test URL',
			'is_active': True,
			'created_at': datetime.utcnow(),
			'updated_at': datetime.utcnow(),
		},
	)
print('ready: short_code=abc123')
PY
```

## 3) Choose a hot short code

Pick any existing active short code from your `urls` table. Example shown as `abc123`.

## 4) Run Gold tsunami test — choose a variant

### Option A: Arrival-rate test (100 req/sec)

Run k6 in Docker (no host install needed):

```bash
docker run --rm --network host \
	-e BASE_URL=http://localhost:8080 \
	-e HOT_PATH=/abc123 \
	-v "$PWD/loadtest/k6:/scripts" \
	grafana/k6 run /scripts/gold.js
```

What this test does:
- Ramps from 20 → 40 → 80 → 100 iterations/sec (arrival rate)
- Sends mostly redirect traffic (cache-hot path)
- Enforces `http_req_failed < 5%`
- Enforces `p(95) < 3000ms`

### Option B: 500 VU concurrent users test

```bash
docker run --rm --network host \
	-e BASE_URL=http://localhost:8080 \
	-e HOT_PATH=/abc123 \
	-v "$PWD/loadtest/k6:/scripts" \
	grafana/k6 run /scripts/gold-500vus.js
```

What this test does:
- Ramps 0 → 100 → 300 → 500 VUs in stages
- Holds at 500 VUs for 2 minutes
- 85% of traffic hits the redirect path (cache-hot), 15% hits `/health`
- Enforces `http_req_failed < 5%`
- Enforces `p(95) < 3000ms`

## 5) Capture cache evidence

Run twice and compare headers:

```bash
curl -I http://localhost:8080/abc123
curl -I http://localhost:8080/abc123
```

Expected header behavior:
- first call may be `X-Cache: MISS` if cache is cold
- subsequent calls should be `X-Cache: HIT`

## 6) Record required verification artifacts

- Terminal screenshot of k6 run showing thresholds pass/fail.
- `docker ps` screenshot showing app fleet + nginx + redis.
- p95 latency from k6 output (`http_req_duration p(95)`).
- Error rate from k6 output (`http_req_failed`).
- Cache proof from `X-Cache` headers.

## 7) Bottleneck Report template (2-3 sentences)

Before optimization, the redirect path hit PostgreSQL for every request, which became the primary bottleneck under high concurrency due to repeated indexed lookups and connection pressure. We added Redis caching for short-code resolution and invalidation on URL update/delete, shifting repeat reads from disk-backed DB access to in-memory lookups. This reduced p95 latency and kept `http_req_failed` under 5% during 500-user load.

## 8) Tear down

```bash
docker compose -f docker-compose.gold.yml down
```
