import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request
from peewee import DoesNotExist

from app.cache import cache, redirect_cache_key
from app.models.url import Url
from app.utils import generate_short_code

urls_crud_bp = Blueprint("urls_crud", __name__, url_prefix="/urls")

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _url_dict(url):
    return {
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "updated_at": url.updated_at.isoformat() if url.updated_at else None,
    }


def _p(*keys):
    """Pull values from query string or JSON body."""
    args = request.args
    body = request.get_json(silent=True) or {}
    return {k: args.get(k) if args.get(k) is not None else body.get(k) for k in keys}


@urls_crud_bp.route("/bulk", methods=["POST"])
def bulk_load():
    data = request.get_json(silent=True) or {}
    filename = data.get("file", "urls.csv")
    if not filename.endswith(".csv") or "/" in filename or ".." in filename:
        return jsonify(error="Invalid filename"), 400

    csv_path = DATA_DIR / filename
    if not csv_path.exists():
        return jsonify(error=f"{filename} not found on server"), 404

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    from app.database import db
    from peewee import chunked

    records = [
        {
            "id": int(r["id"]),
            "user_id": int(r["user_id"]),
            "short_code": r["short_code"],
            "original_url": r["original_url"],
            "title": r["title"],
            "is_active": r["is_active"].strip().lower() == "true",
            "created_at": datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.strptime(r["updated_at"], "%Y-%m-%d %H:%M:%S"),
        }
        for r in rows
    ]

    with db.atomic():
        for batch in chunked(records, 100):
            Url.insert_many(batch).on_conflict_ignore().execute()

    return jsonify(imported=len(records), file=filename), 201


@urls_crud_bp.route("", methods=["GET"], strict_slashes=False)
def list_urls():
    p = _p("user_id", "is_active", "page", "per_page")
    page = max(1, int(p.get("page") or 1))
    per_page = min(100, max(1, int(p.get("per_page") or 20)))

    query = Url.select().order_by(Url.id)

    if p.get("user_id") is not None:
        query = query.where(Url.user == int(p["user_id"]))

    if p.get("is_active") is not None:
        val = p["is_active"]
        if isinstance(val, str):
            val = val.lower() == "true"
        query = query.where(Url.is_active == val)

    total = query.count()
    items = [_url_dict(u) for u in query.paginate(page, per_page)]

    return jsonify(page=page, per_page=per_page, total=total, items=items), 200


@urls_crud_bp.route("/<int:url_id>", methods=["GET"])
def get_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except DoesNotExist:
        return jsonify(error="URL not found"), 404
    return jsonify(_url_dict(url)), 200


@urls_crud_bp.route("", methods=["POST"], strict_slashes=False)
def create_url():
    # Fractured Vessel: reject non-JSON / malformed bodies
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify(error="Request body must be valid JSON"), 400

    original_url = data.get("original_url", "").strip()
    # Unwitting Stranger: reject missing required fields
    if not original_url:
        return jsonify(error="original_url is required"), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify(error="user_id is required"), 400

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    url = Url.create(
        user_id=int(user_id),
        short_code=generate_short_code(),
        original_url=original_url,
        title=data.get("title", "").strip(),
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    # Prime the redirect cache with the new URL
    cache.set(
        redirect_cache_key(url.short_code),
        json.dumps({"u": url.original_url, "id": url.id, "uid": url.user_id}),
    )

    return jsonify(_url_dict(url)), 201


@urls_crud_bp.route("/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except DoesNotExist:
        return jsonify(error="URL not found"), 404

    data = request.get_json(silent=True) or {}
    changed = False

    for field in ("title", "original_url", "is_active"):
        if field in data:
            setattr(url, field, data[field])
            changed = True

    if changed:
        url.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        url.save()
        # Slumbering Guide: invalidate cache so deactivated URLs stop redirecting
        cache.delete(redirect_cache_key(url.short_code))

    return jsonify(_url_dict(url)), 200


@urls_crud_bp.route("/<int:url_id>", methods=["DELETE"])
def delete_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except DoesNotExist:
        return jsonify(error="URL not found"), 404

    cache.delete(redirect_cache_key(url.short_code))
    url.delete_instance()
    return "", 204
