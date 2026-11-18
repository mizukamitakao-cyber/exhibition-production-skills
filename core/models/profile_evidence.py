from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class EvidenceEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: Literal["confirmed", "documented", "proposed", "unset", "conflict"] = "unset"
    source: str | None = None
    confirmed_at: str | None = None
    note: str = ""


class ProfileEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    museum_id: str
    profile_version: int = 1
    updated_at: str = ""
    # フィールドパス（例: "basic.name"）をキーとする根拠情報辞書
    evidence: dict[str, EvidenceEntry] = Field(default_factory=dict)
