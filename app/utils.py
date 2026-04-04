import secrets
import string

_ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    from app.models.url import Url

    while True:
        code = "".join(secrets.choice(_ALPHABET) for _ in range(length))
        if not Url.select().where(Url.short_code == code).exists():
            return code
