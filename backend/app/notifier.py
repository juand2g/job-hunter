import httpx

from .config import settings
from .models import Job

TELEGRAM_API = "https://api.telegram.org"


async def send_message(text: str) -> bool:
    if not settings.telegram_token or not settings.telegram_chat_id:
        return False
    url = f"{TELEGRAM_API}/bot{settings.telegram_token}/sendMessage"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("ok", False)


def _format_job(job: Job) -> str:
    sal = f" | {job.salary}" if job.salary else ""
    return f"{job.title} — {job.company} [{job.seniority}] score {job.score}{sal}\n{job.url}"


async def notify_new_matches(new_matches: list[Job]) -> bool:
    if not new_matches:
        return True
    top = sorted(new_matches, key=lambda j: j.score, reverse=True)[:10]
    lines = "\n\n".join(_format_job(j) for j in top)
    text = f"Nuevas vacantes con match ({len(new_matches)}):\n\n{lines}"
    return await send_message(text)
