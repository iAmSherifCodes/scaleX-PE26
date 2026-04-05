import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    silver_scaleout: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '15s', target: 50 },
        { duration: '15s', target: 200 },
        { duration: '60s', target: 200 },
        { duration: '10s', target: 0 },
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
const HOT_PATH = __ENV.HOT_PATH || '/4mya84';
const COLD_PATH = __ENV.COLD_PATH || '/health';

export default function () {
  const route = Math.random() < 0.8 ? HOT_PATH : COLD_PATH;
  const res = http.get(`${BASE_URL}${route}`, { tags: { route } });

  check(res, {
    'status is 200/302': (r) => r.status === 200 || r.status === 302,
  });

  sleep(Math.random() * 0.2 + 0.1);
}
