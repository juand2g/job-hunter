from datetime import datetime, timezone

from bson import ObjectId
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import runner
from .application import APPLICATION_STATUSES
from .db import jobs
from .matching.llm_match import match_job, personalize_cv
from .models import Job


def _age_days(doc: dict) -> float | None:
    ref = doc.get("published_at") or doc.get("first_seen")
    if not ref:
        return None
    if isinstance(ref, str):
        try:
            ref = datetime.fromisoformat(ref)
        except ValueError:
            return None
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - ref).total_seconds() / 86400, 1)


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    doc["age_days"] = _age_days(doc)
    return doc


app = FastAPI(title="Job Hunter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"name": "job-hunter", "status": "ok"}


@app.get("/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    latam: bool = False,
    matched: bool = False,
    seniority: str = "",
    source: str = "",
    application_status: str = "",
    max_age: int = 0,
):
    query = {}
    if latam:
        query["latam_friendly"] = True
    if matched:
        query["matched"] = True
        query["latam_friendly"] = True
    if seniority:
        query["seniority"] = seniority
    if source:
        query["source"] = source
    if application_status:
        query["application_status"] = application_status
    sort = [("score", -1), ("fetched_at", -1)] if matched else [("fetched_at", -1)]
    docs = [_serialize(d) for d in await jobs.find(query).sort(sort).to_list(length=5000)]
    if max_age > 0:
        docs = [d for d in docs if d.get("age_days") is None or d["age_days"] <= max_age]
    return {"count": len(docs), "jobs": docs[skip : skip + limit]}


@app.get("/matches")
async def list_matches(
    skip: int = 0,
    limit: int = 50,
    seniority: str = "",
    max_age: int = 0,
):
    query = {"matched": True, "latam_friendly": True}
    if seniority:
        query["seniority"] = seniority
    docs = [_serialize(d) for d in await jobs.find(query).sort([("score", -1), ("fetched_at", -1)]).to_list(length=5000)]
    if max_age > 0:
        docs = [d for d in docs if d.get("age_days") is None or d["age_days"] <= max_age]
    return {"count": len(docs), "jobs": docs[skip : skip + limit]}


@app.get("/stats")
async def stats():
    total = await jobs.count_documents({})
    latam = await jobs.count_documents({"latam_friendly": True})
    by_source = {}
    async for doc in jobs.aggregate([{"$group": {"_id": "$source", "n": {"$sum": 1}}}]):
        by_source[doc["_id"]] = doc["n"]
    by_seniority = {}
    async for doc in jobs.aggregate([{"$group": {"_id": "$seniority", "n": {"$sum": 1}}}]):
        by_seniority[doc["_id"]] = doc["n"]
    return {
        "total": total,
        "latam_friendly": latam,
        "by_source": by_source,
        "by_seniority": by_seniority,
    }


@app.post("/fetch")
async def trigger_fetch():
    await runner.run()
    return {"status": "ok"}


@app.post("/notify_test")
async def notify_test():
    from .notifier import send_message

    try:
        ok = await send_message("Test de JobHunter: la notificacion por Telegram funciona.")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
    if not ok:
        return {
            "status": "error",
            "detail": "Telegram no configurado o el bot no puede escribirte. Asegurate de abrir t.me/Jobhunter12321bot y pulsar /start.",
        }
    return {"status": "ok"}


async def _get_job(job_id: str) -> Job | None:
    try:
        doc = await jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        return None
    if not doc:
        return None
    return Job(**doc)


@app.post("/match/{job_id}")
async def match_endpoint(job_id: str):
    job = await _get_job(job_id)
    if not job:
        return {"status": "error", "detail": "job not found"}
    try:
        result = await match_job(job)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
    return {"status": "ok", "job_id": job_id, "match": result}


@app.post("/cv/{job_id}")
async def cv_endpoint(job_id: str):
    job = await _get_job(job_id)
    if not job:
        return {"status": "error", "detail": "job not found"}
    try:
        cv = await personalize_cv(job)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
    return {"status": "ok", "job_id": job_id, "cv": cv}


class ApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


@app.get("/application-statuses")
async def application_statuses():
    return {"statuses": APPLICATION_STATUSES}


@app.patch("/jobs/{job_id}/application")
async def update_application(job_id: str, update: ApplicationUpdate):
    if update.status is not None and update.status not in APPLICATION_STATUSES:
        return {"status": "error", "detail": "estado inválido"}
    try:
        oid = ObjectId(job_id)
    except Exception:
        return {"status": "error", "detail": "job not found"}
    doc = await jobs.find_one({"_id": oid})
    if not doc:
        return {"status": "error", "detail": "job not found"}
    set_fields = {}
    if update.status is not None:
        set_fields["application_status"] = update.status
    if update.notes is not None:
        set_fields["notes"] = update.notes
    if set_fields:
        await jobs.update_one({"_id": oid}, {"$set": set_fields})
    return {"status": "ok", "job_id": job_id, **set_fields}
