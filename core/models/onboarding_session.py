from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class AnsweredQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question_id: str
    answer: str = ""
    answered_at: str = ""
    source: str = "hearing"  # hearing | document


class PendingQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question_id: str
    phase: str = ""
    priority: str = ""


class SkippedQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question_id: str
    reason: str = ""


class ProvidedDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    filename: str
    extracted_at: str = ""
    fields_updated: list[str] = Field(default_factory=list)


class ConflictRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    field_path: str
    value_a: str = ""
    source_a: str = ""
    value_b: str = ""
    source_b: str = ""
    detected_at: str = ""


class OnboardingSession(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    session_id: str
    museum_id: str
    status: Literal[
        "not_started", "in_progress", "paused",
        "ready_for_review", "approved", "revision_in_progress"
    ] = "not_started"
    created_at: str = ""
    updated_at: str = ""
    paused_at: str | None = None
    paused_reason: str = ""

    current_phase: str = ""
    completed_phases: list[str] = Field(default_factory=list)

    answered_questions: list[AnsweredQuestion] = Field(default_factory=list)
    pending_questions: list[PendingQuestion] = Field(default_factory=list)
    skipped_questions: list[SkippedQuestion] = Field(default_factory=list)

    provided_documents: list[ProvidedDocument] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)

    profile_draft_version: int | None = None
    notes: str = ""
