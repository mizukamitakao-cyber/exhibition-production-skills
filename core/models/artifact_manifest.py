from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Artifact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    artifact_id: str
    type: str = ""  # idea-list | research-memo | plan | story-structure | manuscript | design-concept | review
    title: str = ""
    version: int = 1
    revision: int = 1  # 楽観的競合検出用。更新のたびにインクリメント
    status: Literal["draft", "ready_for_review", "approved", "superseded"] = "draft"
    file_path: str = ""
    sha256: str = ""  # 承認時に計算したSHA-256ハッシュ
    created_at: str = ""
    updated_at: str = ""
    approved_at: str | None = None
    approved_by: str | None = None
    parent_artifact_id: str | None = None
    review_ids: list[str] = Field(default_factory=list)
    approval_ids: list[str] = Field(default_factory=list)


class ArtifactManifest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    project_id: str
    updated_at: str = ""
    artifacts: list[Artifact] = Field(default_factory=list)
