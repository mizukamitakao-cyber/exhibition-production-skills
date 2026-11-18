from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Source(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_id: str  # 例: src-001
    type: str = ""  # primary_source | academic | collection_item | web | interview | other
    title: str = ""
    author: str = ""
    year: int | None = None
    location: str = ""
    pages: str = ""
    retrieved_at: str | None = None
    verification_status: str = ""  # verified | unverified | disputed
    access_permission: str = ""   # permission_obtained | public_domain | unknown | restricted
    local_path: str | None = None
    notes: str = ""


class SourceUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_id: str
    used_in_artifacts: list[str] = Field(default_factory=list)
    sections: str = ""


class SourceRegistry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    project_id: str
    updated_at: str = ""
    sources: list[Source] = Field(default_factory=list)
    source_usage: list[SourceUsage] = Field(default_factory=list)
