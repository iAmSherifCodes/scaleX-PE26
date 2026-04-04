from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from app.auth import assert_owner, require_auth
from app.events import log_event
from app.models.url import Url
from app.utils import generate_short_code

urls_bp = Blueprint("urls", __name__, url_prefix="/api/urls")


@urls_bp.route("/", methods=["POST"])
@require_auth
def create_url():
    data = request.get_json(silent=True) or {}
    original_url = data.get("original_url", "").strip()
    if not original_url:
        return jsonify(error="original_url is required"), 400

    title = data.get("title", "").strip()
    short_code = generate_short_code()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    url = Url.create(
        user_id=g.current_user.id,
        short_code=short_code,
        original_url=original_url,
        title=title,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    log_event(url.id, g.current_user.id, "created", {"short_code": short_code, "original_url": original_url})

    return jsonify(model_to_dict(url)), 201


@urls_bp.route("/<int:url_id>", methods=["GET"])
def get_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except DoesNotExist:
        return jsonify(error="URL not found"), 404
    return jsonify(model_to_dict(url)), 200


@urls_bp.route("/<int:url_id>", methods=["PATCH"])
@require_auth
def update_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except DoesNotExist:
        return jsonify(error="URL not found"), 404

    assert_owner(url, g.current_user)

    data = request.get_json(silent=True) or {}
    allowed = ("title", "original_url", "is_active")

    for field in allowed:
        if field in data:
            setattr(url, field, data[field])
            log_event(url.id, g.current_user.id, "updated", {"field": field, "new_value": str(data[field])})

    url.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    url.save()

    return jsonify(model_to_dict(url)), 200


@urls_bp.route("/<int:url_id>", methods=["DELETE"])
@require_auth
def delete_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except DoesNotExist:
        return jsonify(error="URL not found"), 404

    assert_owner(url, g.current_user)

    url.is_active = False
    url.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    url.save()

    log_event(url.id, g.current_user.id, "deleted", {"reason": "user_requested"})

    return "", 204
