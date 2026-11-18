from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Finding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    finding_id: str
    type: str = ""  # logical_issue | factual_issue | expression_issue | requirement_gap | suggestion
    severity: str = ""  # critical | major | minor | info
    location: str = ""
    description: str = ""
    recommendation: str = ""
    status: Literal["pending", "accepted", "rejected", "deferred"] = "pending"
    resolved_at: str | None = None
    resolution_note: str = ""


class ReviewRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    review_id: str
    artifact_id: str
    reviewer_role: Literal["advocate", "reviewer"]
    reviewed_at: str = ""
    findings: list[Finding] = Field(default_factory=list)
    overall_assessment: str = ""
    proceed_recommendation: bool | None = None
