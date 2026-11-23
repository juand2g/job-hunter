import asyncio

import httpx

from ..config import settings
from ..pipeline.normalize import classify_location

NAME = "torre"
BASE_URL = "https://api.torre.ai/v1"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.torre_api_key}"}


async def fetch(limit: int) -> list[dict]:
    if not settings.torre_api_key:
        return []

    summaries: list[dict] = []
    cursor: str | None = None
    async with httpx.AsyncClient(timeout=30, headers=_headers()) as client:
        while len(summaries) < limit:
            size = min(20, limit - len(summaries))
            body: dict = {"limit": size}
            if cursor:
                body["cursor"] = cursor
            resp = await client.post(f"{BASE_URL}/jobs/search", json=body)
            resp.raise_for_status()
            data = resp.json()
            summaries.extend(data.get("data", []))
            pagination = data.get("pagination", {})
            if not pagination.get("has_more") or not pagination.get("next_cursor"):
                break
            cursor = pagination["next_cursor"]

        details = await asyncio.gather(
            *[_fetch_detail(client, s["job"]["id"]) for s in summaries],
            return_exceptions=True,
        )

    result = []
    for detail in details:
        if isinstance(detail, dict) and detail.get("id"):
            result.append(_normalize(detail))
    return result


async def _fetch_detail(client: httpx.AsyncClient, job_id: str) -> dict:
    resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
    resp.raise_for_status()
    return resp.json()


def _normalize(detail: dict) -> dict:
    place = detail.get("place") or {}
    remote = bool(place.get("remote"))
    anywhere = bool(place.get("anywhere"))
    locations = place.get("locations") or []
    location = ", ".join(locations) or ("Remote" if remote else "")

    orgs = detail.get("organizations") or []
    company = orgs[0] if orgs else ""

    tags = [s.get("name", "") for s in (detail.get("skills") or []) if s.get("name")]

    desc_parts = [detail.get("tagline", "")]
    for d in detail.get("details") or []:
        desc_parts.append(d.get("content", ""))
    description = "\n".join(p for p in desc_parts if p)

    comp = detail.get("compensation") or {}
    salary = ""
    if comp.get("min") or comp.get("max"):
        if comp.get("min") and comp.get("max") and comp["min"] != comp["max"]:
            value = f"{comp['min']}-{comp['max']}"
        else:
            value = str(comp.get("min") or comp.get("max"))
        parts = [value]
        if comp.get("currency"):
            parts.append(comp["currency"])
        if comp.get("periodicity"):
            parts.append(comp["periodicity"])
        salary = " ".join(parts)

    _, latam = classify_location(location, empty_is_latam=remote)

    title_tagline = f"{detail.get('title', '')} {detail.get('tagline', '')}".lower()
    if not latam and any(k in title_tagline for k in ("latam", "latinoamérica", "colombia")):
        latam = True

    return {
        "source": NAME,
        "source_id": detail.get("id", ""),
        "title": detail.get("title", ""),
        "company": company,
        "url": detail.get("url", ""),
        "location": location,
        "tags": tags,
        "job_type": detail.get("type", ""),
        "salary": salary,
        "description": description,
        "published_at": None,
        "remote": remote,
        "latam_friendly": anywhere or latam,
    }
