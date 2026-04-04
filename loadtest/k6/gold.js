import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    tsunami: {
      executor: 'ramping-arrival-rate',
      startRate: 20,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: 500,
      stages: [
        { duration: '30s', target: 40 },
        { duration: '1m', target: 80 },
        { duration: '2m', target: 100 },
        { duration: '1m', target: 100 },
        { duration: '30s', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<3000'],
  },
  maxRedirects: 0,
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const HOT_PATH = __ENV.HOT_PATH || '/abc123';
const COLD_PATH = __ENV.COLD_PATH || '/health';

export default function () {
  // 80/20 traffic split keeps pressure on the cache-hot route.
  const route = Math.random() < 0.8 ? HOT_PATH : COLD_PATH;
  const res = http.get(`${BASE_URL}${route}`, {
    tags: { route },
  });

  check(res, {
    'status is 200/302': (r) => r.status === 200 || r.status === 302,
  });
}
