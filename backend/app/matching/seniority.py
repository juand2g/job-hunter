import re

SENIOR_TITLE_KEYWORDS = [
    "senior",
    "sr",
    "staff",
    "principal",
    "tech lead",
    "team lead",
    "lead engineer",
    "lead developer",
    "lead software",
    "engineering lead",
    "head of",
    "director",
    "cto",
    "vp",
    "arquitecto",
    "architect",
]

JUNIOR_TITLE_KEYWORDS = [
    "junior",
    "jr",
    "entry level",
    "entry-level",
    "trainee",
    "intern",
    "internship",
    "practicante",
    "becario",
    "pasante",
    "new grad",
    "recent graduate",
]

MID_TITLE_KEYWORDS = [
    "mid-level",
    "mid level",
    "mid-senior",
    "semisenior",
    "semi senior",
    "semi-senior",
    "intermediate",
]

SENIOR_YEARS_KEYWORDS = [
    "5+ years",
    "6+ years",
    "7+ years",
    "8+ years",
    "10+ years",
    "5+ años",
    "6 años",
    "7 años",
    "8 años",
    "10 años",
]

JUNIOR_YEARS_KEYWORDS = [
    "0-2 years",
    "1-2 years",
    "1+ year",
    "no experience",
    "entry level",
]

MID_YEARS_KEYWORDS = [
    "2-4 years",
    "2+ years",
    "3+ years",
    "3-5 years",
    "4+ years",
    "2 años",
    "3 años",
    "4 años",
]


def _matches(text: str, keyword: str) -> bool:
    if re.fullmatch(r"[a-z0-9.\-+/]+", keyword):
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None
    return keyword in text


def _any(text: str, keywords: list[str]) -> bool:
    return any(_matches(text, k) for k in keywords)


def classify_seniority(title: str, description: str) -> str:
    title_text = (title or "").lower()

    if _any(title_text, SENIOR_TITLE_KEYWORDS):
        return "senior"
    if _any(title_text, JUNIOR_TITLE_KEYWORDS):
        return "junior"
    if _any(title_text, MID_TITLE_KEYWORDS):
        return "mid"

    desc_text = (description or "").lower()
    if _any(desc_text, SENIOR_YEARS_KEYWORDS):
        return "senior"
    if _any(desc_text, JUNIOR_YEARS_KEYWORDS):
        return "junior"
    if _any(desc_text, MID_YEARS_KEYWORDS):
        return "mid"

    return "unknown"
