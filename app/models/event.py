from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from app.database import BaseModel
from app.models.url import Url
from app.models.user import User


class Event(BaseModel):
    url = ForeignKeyField(Url, backref="events", column_name="url_id")
    user = ForeignKeyField(User, backref="events", column_name="user_id")
    event_type = CharField()  # created | updated | deleted | clicked
    timestamp = DateTimeField()
    details = TextField()  # raw JSON string

    class Meta:
        table_name = "events"
        indexes = (
            (("url_id",), False),        # event history per URL
            (("user_id",), False),       # activity per user
            (("event_type",), False),    # filter clicks for analytics
        )
