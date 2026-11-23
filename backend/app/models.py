from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Job(BaseModel):
    source: str
    source_id: str
    title: str
    company: str
    url: str
    location: str = ""
    tags: list[str] = Field(default_factory=list)
    job_type: str = ""
    salary: str = ""
    description: str = ""
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    first_seen: Optional[datetime] = None
    remote: bool = False
    latam_friendly: bool = False
    score: int = 0
    matched: bool = False
    matched_keywords: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)
    seniority: str = "unknown"
    apply_type: str = "unknown"
    application_status: str = "not_applied"
    notes: str = ""
