import json
import threading
from datetime import datetime, timezone


def log_event(url_id: int, user_id: int, event_type: str, details: dict, async_: bool = False):
    """Log an event. Set async_=True for fire-and-forget (used on redirect clicks)."""
    if async_:
        t = threading.Thread(target=_insert_event, args=(url_id, user_id, event_type, details), daemon=True)
        t.start()
    else:
        _insert_event(url_id, user_id, event_type, details)


def _insert_event(url_id: int, user_id: int, event_type: str, details: dict):
    from app.database import db
    from app.models.event import Event

    # Peewee requires an explicit connection in a new thread
    with db.connection_context():
        Event.create(
            url_id=url_id,
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            details=json.dumps(details),
        )
