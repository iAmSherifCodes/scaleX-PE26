from flask import Blueprint, jsonify, redirect

from app.cache import cache, redirect_cache_key
from app.events import log_event
from app.models.url import Url

redirect_bp = Blueprint("redirect", __name__)


@redirect_bp.route("/<short_code>")
def resolve(short_code):
    cache_key = redirect_cache_key(short_code)
    cached_target = cache.get(cache_key)
    if cached_target:
        response = redirect(cached_target, 302)
        response.headers["X-Cache"] = "HIT"
        return response

    url = (
        Url.select()
        .where(Url.short_code == short_code, Url.is_active == True)
        .first()
    )
    if url is None:
        return jsonify(error="Short URL not found or inactive"), 404

    log_event(url.id, url.user_id, "clicked", {}, async_=True)

    cache.set(cache_key, url.original_url)
    response = redirect(url.original_url, 302)
    response.headers["X-Cache"] = "MISS"
    return response
