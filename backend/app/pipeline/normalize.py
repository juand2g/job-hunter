from datetime import datetime, timezone
from typing import Optional

_LATAM_KEYS = (
    "colombia",
    "latam",
    "latin america",
    "south america",
    "americas",
    "latinoamérica",
    "américa latina",
    "worldwide",
    "anywhere",
    "global",
)

_REMOTE_KEYS = (
    "remote",
    "worldwide",
    "anywhere",
    "global",
    "americas",
)


def classify_location(location: str, empty_is_latam: bool = False) -> tuple[bool, bool]:
    loc = (location or "").lower().strip()
    if not loc:
        return (True, empty_is_latam)
    remote = any(key in loc for key in _REMOTE_KEYS)
    latam = any(key in loc for key in _LATAM_KEYS)
    return (remote, latam)


def parse_epoch(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def parse_iso(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None
