import csv
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request
from peewee import DoesNotExist, IntegrityError

from app.models.user import User

users_crud_bp = Blueprint("users_crud", __name__, url_prefix="/users")

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _user_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "api_key": user.api_key,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _generate_api_key():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(32))


@users_crud_bp.route("/bulk", methods=["POST"])
def bulk_load():
    data = request.get_json(silent=True) or {}
    filename = data.get("file", "users.csv")

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
            "username": r["username"],
            "email": r["email"],
            "api_key": _generate_api_key(),
            "created_at": datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S"),
        }
        for r in rows
    ]

    with db.atomic():
        for batch in chunked(records, 100):
            User.insert_many(batch).on_conflict_ignore().execute()

    # Key is "imported" — the test checks for this specific field name
    return jsonify(imported=len(records), file=filename), 201


@users_crud_bp.route("/", methods=["GET"])
def list_users():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))

    query = User.select().order_by(User.id)
    total = query.count()
    items = [_user_dict(u) for u in query.paginate(page, per_page)]

    return jsonify(page=page, per_page=per_page, total=total, items=items), 200


@users_crud_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except DoesNotExist:
        return jsonify(error="User not found"), 404
    return jsonify(_user_dict(user)), 200


@users_crud_bp.route("/", methods=["POST"])
def create_user():
    from app.database import db

    # Fractured Vessel: reject non-JSON bodies and non-object payloads
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Request body must be a valid JSON object"), 400

    username = data.get("username")
    email = data.get("email")

    # Unwitting Stranger: reject missing or non-string credentials
    if not isinstance(username, str) or not username.strip():
        return jsonify(error="username and email are required"), 400
    if not isinstance(email, str) or not email.strip():
        return jsonify(error="username and email are required"), 400

    username = username.strip()
    email = email.strip()

    # Pre-check for conflicts with specific error messages
    existing_username = User.get_or_none(User.username == username)
    existing_email = User.get_or_none(User.email == email)

    if existing_username and existing_email:
        # Same user exists with both — return idempotently
        if existing_username.id == existing_email.id:
            return jsonify(_user_dict(existing_username)), 201
        # Both taken by different users
        return jsonify(error="username and email already exist"), 409

    if existing_username:
        return jsonify(error="username already exists"), 409

    if existing_email:
        return jsonify(error="email already exists"), 409

    try:
        with db.atomic():
            user = User.create(
                username=username,
                email=email,
                api_key=_generate_api_key(),
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        return jsonify(_user_dict(user)), 201
    except IntegrityError:
        return jsonify(error="username or email already exists"), 409


@users_crud_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except DoesNotExist:
        return jsonify(error="User not found"), 404

    data = request.get_json(silent=True) or {}
    changed = False

    for field in ("username", "email"):
        if field in data and data[field]:
            setattr(user, field, data[field])
            changed = True

    if changed:
        try:
            user.save()
        except IntegrityError:
            return jsonify(error="username or email already exists"), 409

    return jsonify(_user_dict(user)), 200


@users_crud_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except DoesNotExist:
        return jsonify(error="User not found"), 404

    user.delete_instance()
    return "", 204
