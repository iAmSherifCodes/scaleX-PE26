from flask import Blueprint, jsonify, request
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from app.models.event import Event
from app.models.url import Url

events_bp = Blueprint("events", __name__, url_prefix="/api/urls")


@events_bp.route("/<int:url_id>/events", methods=["GET"])
def list_url_events(url_id):
    try:
        Url.get_by_id(url_id)
    except DoesNotExist:
        return jsonify(error="URL not found"), 404

    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))

    query = Event.select().where(Event.url == url_id).order_by(Event.timestamp.desc())
    total = query.count()
    items = list(query.paginate(page, per_page))

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [model_to_dict(e, recurse=False) for e in items],
    }), 200
