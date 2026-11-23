from datetime import datetime

from .application import detect_apply_type
from .config import settings
from .db import jobs
from .matching.scorer import score_job
from .matching.seniority import classify_seniority
from .models import Job
from .notifier import notify_new_matches
from .sources import ALL

async def run() -> None:
    processed = 0
    new = 0
    new_matches: list[Job] = []
    for source in ALL:
        try:
            fetched = await source.fetch(settings.fetch_limit)
        except Exception as exc:
            print(f"[{source.NAME}] ERROR: {exc}")
            continue

        for raw in fetched:
            job = Job(**raw)
            score, matched_kw, excluded_kw = score_job(job.title, job.description, job.tags)
            job.score = score
            job.matched_keywords = matched_kw
            job.excluded_keywords = excluded_kw
            job.matched = score > 0 and not excluded_kw
            job.seniority = classify_seniority(job.title, job.description)
            job.apply_type = detect_apply_type(job.url)
            result = await jobs.update_one(
                {"source": job.source, "source_id": job.source_id},
                {
                    "$set": job.model_dump(exclude={"first_seen", "application_status", "notes"}),
                    "$setOnInsert": {
                        "first_seen": datetime.utcnow(),
                        "application_status": "not_applied",
                        "notes": "",
                    },
                },
                upsert=True,
            )
            processed += 1
            if result.upserted_id:
                new += 1
                if (
                    job.matched
                    and job.latam_friendly
                    and job.score >= settings.match_score_threshold
                ):
                    new_matches.append(job)
        print(f"[{source.NAME}] fetched {len(fetched)}")

    print(f"done: {processed} processed, {new} new")
    if new_matches:
        await notify_new_matches(new_matches)
        print(f"[telegram] notificadas {len(new_matches)} vacantes nuevas")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
