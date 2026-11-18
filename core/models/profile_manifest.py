"""承認済みプロファイルのマニフェスト（版管理・SHA-256保存）。OI-06解決。"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field


class ProfileEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    version: int
    filename: str
    sha256: str
    approved_at: str
    approved_by: str | None = None


class ProfileManifest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    museum_id: str
    entries: list[ProfileEntry] = Field(default_factory=list)
