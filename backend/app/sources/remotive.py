import httpx

from ..pipeline.normalize import classify_location, parse_iso

NAME = "remotive"
URL = "https://remotive.com/api/remote-jobs"


async def fetch(limit: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(URL, params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()

    return [_normalize(raw) for raw in data.get("jobs", [])]


def _normalize(raw: dict) -> dict:
    location = raw.get("candidate_required_location") or ""
    remote, latam = classify_location(location)
    return {
        "source": NAME,
        "source_id": str(raw.get("id") or ""),
        "title": raw.get("title") or "",
        "company": raw.get("company_name") or "",
        "url": raw.get("url") or "",
        "location": location,
        "tags": raw.get("tags") or [],
        "job_type": raw.get("job_type") or "",
        "salary": raw.get("salary") or "",
        "description": raw.get("description") or "",
        "published_at": parse_iso(raw.get("publication_date")),
        "remote": remote,
        "latam_friendly": latam,
    }
