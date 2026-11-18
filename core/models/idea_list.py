"""アイディア一覧モデル。Idea Generator の出力管理。"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class IdeaEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str = ""
    concept: str = ""
    key_themes: list[str] = Field(default_factory=list)
    target_visitors: list[str] = Field(default_factory=list)
    unique_points: list[str] = Field(default_factory=list)
    estimated_duration: str = ""
    status: Literal["proposed", "selected", "rejected"] = "proposed"
    selected_at: str | None = None
    rejection_reason: str = ""
    notes: str = ""


class IdeaList(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    project_id: str
    museum_id: str
    brief_summary: str = ""
    ideas: list[IdeaEntry] = Field(default_factory=list)
    selected_idea_id: str | None = None
    generated_at: str = ""
    updated_at: str = ""
