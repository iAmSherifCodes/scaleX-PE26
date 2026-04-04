from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from app.database import BaseModel
from app.models.user import User


class Url(BaseModel):
    user = ForeignKeyField(User, backref="urls", column_name="user_id")
    short_code = CharField(6, unique=True)
    original_url = TextField()
    title = CharField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    class Meta:
        table_name = "urls"
        indexes = (
            (("short_code",), True),   # unique — primary redirect lookup
            (("user_id",), False),     # list URLs by user
        )
