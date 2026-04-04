from flask import Blueprint, jsonify, redirect

from app.events import log_event
from app.models.url import Url

redirect_bp = Blueprint("redirect", __name__)


@redirect_bp.route("/<short_code>")
def resolve(short_code):
    url = (
        Url.select()
        .where(Url.short_code == short_code, Url.is_active == True)
        .first()
    )
    if url is None:
        return jsonify(error="Short URL not found or inactive"), 404

    log_event(url.id, url.user_id, "clicked", {}, async_=True)

    return redirect(url.original_url, 302)
