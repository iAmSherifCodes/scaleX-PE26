import os

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class CacheClient:
    def __init__(self):
        self.enabled = False
        self.ttl = int(os.environ.get("CACHE_TTL_SECONDS", "60"))
        self._client = None

    def init_app(self):
        redis_url = os.environ.get("REDIS_URL", "").strip()
        if not redis_url or redis is None:
            self.enabled = False
            return

        try:
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self._client = client
            self.enabled = True
        except Exception:
            self.enabled = False
            self._client = None

    def get(self, key: str):
        if not self.enabled or self._client is None:
            return None
        return self._client.get(key)

    def set(self, key: str, value: str):
        if not self.enabled or self._client is None:
            return
        self._client.setex(key, self.ttl, value)

    def delete(self, key: str):
        if not self.enabled or self._client is None:
            return
        self._client.delete(key)


cache = CacheClient()


def redirect_cache_key(short_code: str) -> str:
    return f"redirect:{short_code}"