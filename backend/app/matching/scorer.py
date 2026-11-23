import unicodedata

from . import keywords

TITLE_WEIGHT = 3
TECH_WEIGHT = 1


def _norm(text: str) -> str:
    t = (text or "").lower()
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def score_job(title: str, description: str, tags: list[str]) -> tuple[int, list[str], list[str]]:
    title_text = _norm(title)
    body_text = _norm(f"{description or ''} {' '.join(tags or [])}")

    excluded = [k for k in keywords.EXCLUDE_KEYWORDS if k in title_text or k in body_text]
    if excluded:
        return (0, [], excluded)

    title_hits = [k for k in keywords.TITLE_KEYWORDS if k in title_text]
    tech_hits = [k for k in keywords.TECH_KEYWORDS if k in body_text]

    score = len(title_hits) * TITLE_WEIGHT + len(tech_hits) * TECH_WEIGHT
    return (score, title_hits + tech_hits, excluded)
