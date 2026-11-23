AUTOMATABLE = {"greenhouse", "lever", "workable", "ashby"}

APPLICATION_STATUSES = [
    "not_applied",
    "saved",
    "applied",
    "follow_up",
    "interview",
    "offer",
    "rejected",
    "not_interested",
]


def detect_apply_type(url: str) -> str:
    u = (url or "").lower()
    if "greenhouse" in u:
        return "greenhouse"
    if "lever.co" in u or "jobs.lever" in u:
        return "lever"
    if "workable" in u:
        return "workable"
    if "ashby" in u:
        return "ashby"
    if "bamboohr" in u:
        return "bamboohr"
    if "torre.ai" in u or "torre.co" in u:
        return "torre"
    if "remoteok" in u:
        return "remoteok"
    if "remotive" in u:
        return "remotive"
    if "linkedin" in u:
        return "linkedin"
    if "indeed" in u:
        return "indeed"
    if not u:
        return "unknown"
    return "custom"
