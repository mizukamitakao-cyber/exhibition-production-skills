from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class MuseumBasic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = ""
    type: str = ""  # museum | archive | cultural_facility | other
    purpose: str = ""
    domains: list[str] = Field(default_factory=list)


class MuseumVisitors(BaseModel):
    model_config = ConfigDict(extra="ignore")
    target_groups: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    accessibility_requirements: list[str] = Field(default_factory=list)


class ExhibitionPolicy(BaseModel):
    model_config = ConfigDict(extra="ignore")
    purpose: str = ""
    education_policy: str = ""
    key_themes: list[str] = Field(default_factory=list)
    content_restrictions: list[str] = Field(default_factory=list)


class Research(BaseModel):
    model_config = ConfigDict(extra="ignore")
    priority_sources: list[str] = Field(default_factory=list)
    citation_style: str = ""
    unverified_handling: str = ""
    ai_content_policy: str = ""


class Writing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    style: str = ""
    honorific_level: str = ""
    max_chars_panel: int | None = None
    max_chars_caption: int | None = None
    vocabulary: dict[str, list[str]] = Field(default_factory=dict)
    notation_rules: list[str] = Field(default_factory=list)


class Design(BaseModel):
    model_config = ConfigDict(extra="ignore")
    design_guide_path: str | None = None
    panel_specs: dict = Field(default_factory=dict)


class Quality(BaseModel):
    model_config = ConfigDict(extra="ignore")
    advocate_criteria: list[str] = Field(default_factory=list)
    reviewer_criteria: list[str] = Field(default_factory=list)


class Operations(BaseModel):
    model_config = ConfigDict(extra="ignore")
    approval_flow: list[str] = Field(default_factory=list)
    roles: dict[str, str] = Field(default_factory=dict)
    output_formats: list[str] = Field(default_factory=list)


class DataManagement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ai_input_restrictions: list[str] = Field(default_factory=list)
    storage_path: str = ""
    backup_policy: str = ""


class MuseumProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    museum_id: str
    profile_version: int = 1
    status: Literal["draft", "ready_for_review", "approved", "revision_in_progress"] = "draft"
    created_at: str = ""
    updated_at: str = ""
    approved_at: str | None = None
    approved_by: str | None = None

    basic: MuseumBasic = Field(default_factory=MuseumBasic)
    visitors: MuseumVisitors = Field(default_factory=MuseumVisitors)
    exhibition_policy: ExhibitionPolicy = Field(default_factory=ExhibitionPolicy)
    research: Research = Field(default_factory=Research)
    writing: Writing = Field(default_factory=Writing)
    design: Design = Field(default_factory=Design)
    quality: Quality = Field(default_factory=Quality)
    operations: Operations = Field(default_factory=Operations)
    data_management: DataManagement = Field(default_factory=DataManagement)
