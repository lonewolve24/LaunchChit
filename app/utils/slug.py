import re
import secrets
import string

_ALNUM = string.ascii_lowercase + string.digits


def slugify_name_segment(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def random_suffix(length: int = 6) -> str:
    return "".join(secrets.choice(_ALNUM) for _ in range(length))


def build_product_slug(name: str) -> str:
    base = slugify_name_segment(name)
    if not base:
        raise ValueError("Name must contain at least one letter or number")
    return f"{base}-{random_suffix()}"
