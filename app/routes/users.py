from flask import Blueprint, jsonify, request
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from app.models.event import Event
from app.models.url import Url
from app.models.user import User

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def _paginate(query, page, per_page):
    total = query.count()
    items = list(query.paginate(page, per_page))
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [model_to_dict(i, recurse=False) for i in items],
    }


@users_bp.route("/<int:user_id>/urls", methods=["GET"])
def list_user_urls(user_id):
    try:
        User.get_by_id(user_id)
    except DoesNotExist:
        return jsonify(error="User not found"), 404

    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))

    query = Url.select().where(Url.user == user_id).order_by(Url.created_at.desc())
    return jsonify(_paginate(query, page, per_page)), 200


@users_bp.route("/<int:user_id>/events", methods=["GET"])
def list_user_events(user_id):
    try:
        User.get_by_id(user_id)
    except DoesNotExist:
        return jsonify(error="User not found"), 404

    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))

    query = Event.select().where(Event.user == user_id).order_by(Event.timestamp.desc())
    return jsonify(_paginate(query, page, per_page)), 200
