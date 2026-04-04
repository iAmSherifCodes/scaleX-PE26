from peewee import CharField, DateTimeField

from app.database import BaseModel


class User(BaseModel):
    username = CharField(unique=True)
    email = CharField(unique=True)
    api_key = CharField(null=True, unique=True)
    created_at = DateTimeField()

    class Meta:
        table_name = "users"
        indexes = (
            (("username",), True),
            (("email",), True),
            (("api_key",), False),
        )
