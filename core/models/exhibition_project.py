from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class ExhibitionBrief(BaseModel):
    model_config = ConfigDict(extra="ignore")
    theme: str = ""
    target_visitors: list[str] = Field(default_factory=list)
    period: str = ""
    venue: str = ""
    constraints: list[str] = Field(default_factory=list)


class ExhibitionProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    project_id: str
    museum_id: str
    profile_version: int = 1
    title: str = ""
    type: Literal["new", "revision"] = "new"
    status: Literal[
        "planning", "in_progress", "review",
        "approved", "completed", "suspended"
    ] = "planning"
    created_at: str = ""
    updated_at: str = ""
    revision_source: str | None = None

    brief: ExhibitionBrief = Field(default_factory=ExhibitionBrief)

    current_phase: str = ""
    completed_phases: list[str] = Field(default_factory=list)
    director_notes: str = ""
