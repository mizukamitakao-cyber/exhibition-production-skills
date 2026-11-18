from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    approval_id: str
    artifact_id: str
    artifact_version: int | None = None
    decision: Literal["approved", "rejected", "conditional_approval"]
    decided_at: str = ""
    decided_by: str = ""
    conditions: list[str] = Field(default_factory=list)
    rejection_reason: str = ""
    notes: str = ""
    review_record_ids: list[str] = Field(default_factory=list)
    previous_approval_id: str | None = None
