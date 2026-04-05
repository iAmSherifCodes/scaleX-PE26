import csv
import secrets
import string
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from peewee import chunked

from app.cache import cache
from app.database import db, init_db
from app.routes import register_routes

_DATA_DIR = Path(__file__).parent.parent / "data"


def _gen_key():
    alpha = string.ascii_letters + string.digits
    return "".join(secrets.choice(alpha) for _ in range(32))


def _parse_dt(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def _bootstrap_db():
    """Create tables and seed from CSVs if tables are empty. Safe to call on every startup."""
    from app.models.user import User
    from app.models.url import Url
    from app.models.event import Event

    try:
        db.connect(reuse_if_open=True)
        db.create_tables([User, Url, Event], safe=True)

        if User.select().count() == 0:
            csv_path = _DATA_DIR / "users.csv"
            if csv_path.exists():
                with open(csv_path, newline="") as f:
                    rows = list(csv.DictReader(f))
                records = [
                    {
                        "id": int(r["id"]),
                        "username": r["username"],
                        "email": r["email"],
                        "api_key": _gen_key(),
                        "created_at": _parse_dt(r["created_at"]),
                    }
                    for r in rows
                ]
                with db.atomic():
                    for batch in chunked(records, 100):
                        User.insert_many(batch).on_conflict_ignore().execute()

        if Url.select().count() == 0:
            csv_path = _DATA_DIR / "urls.csv"
            if csv_path.exists():
                with open(csv_path, newline="") as f:
                    rows = list(csv.DictReader(f))
                valid_user_ids = set(User.select(User.id).tuples())
                valid_user_ids = {uid for (uid,) in valid_user_ids}
                records = [
                    {
                        "id": int(r["id"]),
                        "user_id": int(r["user_id"]),
                        "short_code": r["short_code"],
                        "original_url": r["original_url"],
                        "title": r["title"],
                        "is_active": r["is_active"].strip().lower() == "true",
                        "created_at": _parse_dt(r["created_at"]),
                        "updated_at": _parse_dt(r["updated_at"]),
                    }
                    for r in rows
                    if int(r["user_id"]) in valid_user_ids
                ]
                with db.atomic():
                    for batch in chunked(records, 100):
                        Url.insert_many(batch).on_conflict_ignore().execute()

        if Event.select().count() == 0:
            csv_path = _DATA_DIR / "events.csv"
            if csv_path.exists():
                with open(csv_path, newline="") as f:
                    rows = list(csv.DictReader(f))
                valid_url_ids = {uid for (uid,) in Url.select(Url.id).tuples()}
                records = [
                    {
                        "id": int(r["id"]),
                        "url_id": int(r["url_id"]),
                        "user_id": int(r["user_id"]),
                        "event_type": r["event_type"],
                        "timestamp": _parse_dt(r["timestamp"]),
                        "details": r["details"],
                    }
                    for r in rows
                    if int(r["url_id"]) in valid_url_ids and int(r["user_id"]) in valid_user_ids
                ]
                with db.atomic():
                    for batch in chunked(records, 100):
                        Event.insert_many(batch).on_conflict_ignore().execute()

    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        if not db.is_closed():
            db.close()


def create_app():
    load_dotenv()

    app = Flask(__name__)

    init_db(app)
    cache.init_app()

    from app import models  # noqa: F401 — registers models with Peewee

    _bootstrap_db()

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    return app
