import httpx

from ..pipeline.normalize import classify_location, parse_epoch

NAME = "remoteok"
URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; job-hunter/0.1)"}


async def fetch(limit: int) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        resp = await client.get(URL)
        resp.raise_for_status()
        data = resp.json()

    result = []
    for raw in data[1:]:
        result.append(_normalize(raw))
    return result[:limit]


def _format_salary(raw: dict) -> str:
    smin = raw.get("salary_min")
    smax = raw.get("salary_max")
    if not smin and not smax:
        return ""

    def fmt(n):
        return f"{n:,}" if n is not None else ""

    if smin and smax and smin != smax:
        return f"{fmt(smin)}–{fmt(smax)}"
    return fmt(smin or smax)


def _normalize(raw: dict) -> dict:
    location = raw.get("location") or ""
    remote, latam = classify_location(location, empty_is_latam=True)
    salary = _format_salary(raw)
    return {
        "source": NAME,
        "source_id": str(raw.get("id") or raw.get("slug") or ""),
        "title": raw.get("position") or "",
        "company": raw.get("company") or "",
        "url": raw.get("url") or raw.get("apply_url") or "",
        "location": location,
        "tags": raw.get("tags") or [],
        "job_type": raw.get("job_type") or "",
        "salary": salary,
        "description": raw.get("description") or "",
        "published_at": parse_epoch(raw.get("date")),
        "remote": remote,
        "latam_friendly": latam,
    }
