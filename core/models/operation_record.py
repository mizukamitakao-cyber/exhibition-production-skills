from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Operation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    operation_id: str
    timestamp: str
    operation: Literal["write", "read", "delete", "approve", "reject", "backup", "restore"]
    target_path: str
    actor: str
    session_context: str = ""
    success: bool = True
    error: str | None = None
    details: dict = Field(default_factory=dict)


class OperationRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    museum_id: str
    operations: list[Operation] = Field(default_factory=list)
