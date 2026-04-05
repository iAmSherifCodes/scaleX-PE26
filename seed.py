"""
Seed script — loads users.csv, urls.csv, events.csv into the database.

Usage:
    uv run seed.py

CSV files are expected one directory above the project root:
    ../users.csv
    ../urls.csv
    ../events.csv
"""

import csv
import os
import secrets
import string
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from peewee import chunked

load_dotenv()

# Bootstrap the app so models + DB proxy are initialized
from app import create_app  # noqa: E402

app = create_app()

from app.database import db  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.url import Url  # noqa: E402
from app.models.user import User  # noqa: E402

CSV_DIR = Path(__file__).parent / "data"  # CSV files in data/ directory


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def _generate_api_key() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(32))


def seed_users(path: Path) -> None:
    print(f"Seeding users from {path} ...")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    data = [
        {
            "id": int(r["id"]),
            "username": r["username"],
            "email": r["email"],
            "api_key": _generate_api_key(),
            "created_at": parse_dt(r["created_at"]),
        }
        for r in rows
    ]

    with db.atomic():
        for batch in chunked(data, 100):
            User.insert_many(batch).on_conflict_ignore().execute()

    print(f"  Inserted {len(data)} users.")


def seed_urls(path: Path) -> None:
    print(f"Seeding URLs from {path} ...")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    data = [
        {
            "id": int(r["id"]),
            "user_id": int(r["user_id"]),
            "short_code": r["short_code"],
            "original_url": r["original_url"],
            "title": r["title"],
            "is_active": r["is_active"].strip().lower() == "true",
            "created_at": parse_dt(r["created_at"]),
            "updated_at": parse_dt(r["updated_at"]),
        }
        for r in rows
    ]

    with db.atomic():
        for batch in chunked(data, 100):
            Url.insert_many(batch).on_conflict_ignore().execute()

    print(f"  Inserted {len(data)} URLs.")


def seed_events(path: Path) -> None:
    print(f"Seeding events from {path} ...")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    data = [
        {
            "id": int(r["id"]),
            "url_id": int(r["url_id"]),
            "user_id": int(r["user_id"]),
            "event_type": r["event_type"],
            "timestamp": parse_dt(r["timestamp"]),
            "details": r["details"],
        }
        for r in rows
    ]

    with db.atomic():
        for batch in chunked(data, 100):
            Event.insert_many(batch).on_conflict_ignore().execute()

    print(f"  Inserted {len(data)} events.")


def main():
    with app.app_context():
        print("Creating tables ...")
        db.create_tables([User, Url, Event], safe=True)

        seed_users(CSV_DIR / "users.csv")
        seed_urls(CSV_DIR / "urls.csv")
        seed_events(CSV_DIR / "events.csv")

        # Reset auto-increment sequences after seeding with explicit IDs
        for table in ("users", "urls", "events"):
            db.execute_sql(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
            )

        print("\nDone! Sample API keys (first 5 users):")
        for user in User.select().order_by(User.id).limit(5):
            print(f"  user_id={user.id}  username={user.username}  api_key={user.api_key}")


if __name__ == "__main__":
    main()
