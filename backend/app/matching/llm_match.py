import json

from ..llm import chat
from ..models import Job
from ..profile import PROFILE

_MATCH_SYSTEM = (
    "You are a technical recruiter evaluating a candidate against a job posting. "
    "Be objective and honest. Respond ONLY with valid JSON (no markdown fences)."
)


async def match_job(job: Job) -> dict:
    user = f"""Candidate profile:
{PROFILE}

Job posting:
Title: {job.title}
Company: {job.company}
Salary: {job.salary or 'not disclosed'}
Tags: {', '.join(job.tags)}
Description:
{job.description[:6000]}

Return a JSON object with exactly these keys:
- "score": integer 0-100 (overall fit for the candidate)
- "reasoning": short explanation (2-3 sentences)
- "key_requirements": array of the main requirements from the posting
- "matched_skills": array of candidate skills that match the posting
- "gaps": array of requirements the candidate does not clearly meet
"""
    raw = await chat(
        [{"role": "system", "content": _MATCH_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.1,
        json_mode=True,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"score": None, "reasoning": raw, "key_requirements": [], "matched_skills": [], "gaps": []}


_CV_SYSTEM = (
    "You are a career coach. Rewrite the candidate's CV to emphasize the skills and "
    "experience most relevant to the target job. Keep every fact strictly from the "
    "candidate profile; do NOT invent experience, dates, or skills. Return a complete "
    "CV in clean Markdown."
)


async def personalize_cv(job: Job) -> str:
    user = f"""Candidate profile:
{PROFILE}

Target job:
Title: {job.title}
Company: {job.company}
Description:
{job.description[:6000]}

Write the tailored CV in Markdown. Reorder/emphasize the most relevant skills and
achievements for this role, and adjust the summary to target it. Keep it concise
(max ~1 page)."""
    return await chat(
        [{"role": "system", "content": _CV_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.3,
    )
