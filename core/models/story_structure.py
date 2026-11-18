"""展示構成表モデル。Story Designer の出力管理。"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StorySection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    section_id: str
    title: str = ""
    narrative: str = ""
    key_messages: list[str] = Field(default_factory=list)
    exhibit_items: list[str] = Field(default_factory=list)
    panel_count: int = 0
    display_order: int = 0


class StoryStructure(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    project_id: str
    version: int = 1
    status: Literal["draft", "ready_for_review", "approved"] = "draft"
    overall_narrative: str = ""
    sections: list[StorySection] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
