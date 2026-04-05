import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request
from peewee import DoesNotExist

from app.models.event import Event

events_crud_bp = Blueprint("events_crud", __name__, url_prefix="/events")

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _event_dict(event):
    details = event.details
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "details": details,
    }


def _p(*keys):
    """Pull values from query string or JSON body."""
    args = request.args
    body = request.get_json(silent=True) or {}
    return {k: args.get(k) if args.get(k) is not None else body.get(k) for k in keys}


@events_crud_bp.route("/bulk", methods=["POST"])
def bulk_load():
    data = request.get_json(silent=True) or {}
    filename = data.get("file", "events.csv")
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
            "url_id": int(r["url_id"]),
            "user_id": int(r["user_id"]),
            "event_type": r["event_type"],
            "timestamp": datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S"),
            "details": r["details"],
        }
        for r in rows
    ]

    with db.atomic():
        for batch in chunked(records, 100):
            Event.insert_many(batch).on_conflict_ignore().execute()

    return jsonify(loaded=len(records), file=filename), 201


@events_crud_bp.route("", methods=["GET"], strict_slashes=False)
def list_events():
    p = _p("url_id", "user_id", "event_type", "page", "per_page")
    page = max(1, int(p.get("page") or 1))
    per_page = min(100, max(1, int(p.get("per_page") or 20)))

    query = Event.select().order_by(Event.timestamp.desc())

    if p.get("url_id") is not None:
        query = query.where(Event.url == int(p["url_id"]))
    if p.get("user_id") is not None:
        query = query.where(Event.user == int(p["user_id"]))
    if p.get("event_type") is not None:
        query = query.where(Event.event_type == p["event_type"])

    total = query.count()
    items = [_event_dict(e) for e in query.paginate(page, per_page)]

    return jsonify(page=page, per_page=per_page, total=total, items=items), 200


@events_crud_bp.route("", methods=["POST"], strict_slashes=False)
def create_event():
    data = request.get_json(silent=True) or {}
    url_id = data.get("url_id")
    user_id = data.get("user_id")
    event_type = data.get("event_type", "").strip()
    details = data.get("details", {})

    if not url_id or not event_type:
        return jsonify(error="url_id and event_type are required"), 400

    event = Event.create(
        url_id=int(url_id),
        user_id=int(user_id) if user_id is not None else None,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        details=json.dumps(details) if isinstance(details, dict) else (details or "{}"),
    )

    return jsonify(_event_dict(event)), 201
