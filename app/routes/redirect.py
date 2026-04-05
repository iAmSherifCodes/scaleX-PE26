import json

from flask import Blueprint, jsonify, redirect

from app.cache import cache, redirect_cache_key
from app.events import log_event
from app.models.url import Url

redirect_bp = Blueprint("redirect", __name__)


@redirect_bp.route("/<short_code>")
def resolve(short_code):
    cache_key = redirect_cache_key(short_code)
    cached_value = cache.get(cache_key)

    if cached_value:
        # Cache value is JSON: {"u": original_url, "id": url_id, "uid": user_id}
        # Fall back to plain string for backwards-compatibility.
        try:
            meta = json.loads(cached_value)
            original_url = meta["u"]
            url_id = meta.get("id")
            user_id = meta.get("uid")
        except (json.JSONDecodeError, KeyError, TypeError):
            original_url = cached_value
            url_id = user_id = None

        # Slumbering Guide: verify URL is still active even on cache hit.
        if url_id:
            active = Url.select().where(Url.id == url_id, Url.is_active == True).exists()
            if not active:
                cache.delete(cache_key)
                return jsonify(error="Short URL not found or inactive"), 404

        # Unseen Observer: log every redirect, even cache hits.
        if url_id:
            log_event(url_id, user_id, "clicked", {})

        response = redirect(original_url, 302)
        response.headers["X-Cache"] = "HIT"
        return response

    url = (
        Url.select()
        .where(Url.short_code == short_code, Url.is_active == True)
        .first()
    )
    if url is None:
        return jsonify(error="Short URL not found or inactive"), 404

    log_event(url.id, url.user_id, "clicked", {})

    cache.set(cache_key, json.dumps({"u": url.original_url, "id": url.id, "uid": url.user_id}))
    response = redirect(url.original_url, 302)
    response.headers["X-Cache"] = "MISS"
    return response
