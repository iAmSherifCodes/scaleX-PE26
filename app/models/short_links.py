import string
import secrets
from datetime import datetime, timezone
from peewee import CharField, DateTimeField, IntegerField

from app.database import BaseModel


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    # Use secrets instead of random for cryptographically secure selection
    return "".join(secrets.choice(chars) for _ in range(length))


class ShortLink(BaseModel):
    class Meta:
        table_name = "short_links"

    short_code = CharField(unique=True, max_length=20, index=True)
    original_url = CharField(max_length=2048)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    click_count = IntegerField(default=0)

    @classmethod
    def create_link(cls, original_url):
        # Ensure uniqueness
        for _ in range(5):
            code = generate_short_code()
            if not cls.select().where(cls.short_code == code).exists():
                return cls.create(short_code=code, original_url=original_url)
        raise ValueError("Could not generate a unique short code. Try again.")

    @classmethod
    def get_by_code(cls, short_code):
        # Using peewee's native get_or_none helper to simplify lookup
        return cls.get_or_none(cls.short_code == short_code)

    def increment_clicks(self):
        # Using an atomic SQL update query to avoid race conditions
        # (prefer this over self.click_count += 1; self.save())
        ShortLink.update(click_count=ShortLink.click_count + 1).where(
            ShortLink.id == self.id
        ).execute()
