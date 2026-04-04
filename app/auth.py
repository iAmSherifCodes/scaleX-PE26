from functools import wraps

from flask import g, jsonify, request
from peewee import DoesNotExist


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify(error="Missing X-API-Key header"), 401

        from app.models.user import User
        try:
            g.current_user = User.get(User.api_key == api_key)
        except DoesNotExist:
            return jsonify(error="Invalid API key"), 401

        return f(*args, **kwargs)
    return decorated


def assert_owner(url, user):
    if url.user_id != user.id:
        from flask import abort
        abort(403)
