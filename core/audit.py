"""
監査ログ（operation-log.yaml への追記）
設計仕様: docs/design/05_STORAGE_SECURITY_DESIGN.md §6
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

JST = timezone(timedelta(hours=9))


def _now_jst() -> str:
    return datetime.now(JST).isoformat()


def _load_log(log_path: Path, museum_id: str) -> dict:
    yaml = YAML()
    if not log_path.exists():
        return {"schema_version": "1.0", "museum_id": museum_id, "operations": []}
    with open(log_path, encoding="utf-8") as f:
        data = yaml.load(f)
    return data or {"schema_version": "1.0", "museum_id": museum_id, "operations": []}


class AuditLogger:
    """operation-log.yaml への追記を担当する。"""

    def __init__(self, log_path: Path, museum_id: str) -> None:
        self.log_path = log_path
        self.museum_id = museum_id

    def log(
        self,
        operation: str,
        target_path: str,
        actor: str,
        success: bool = True,
        error: str | None = None,
        details: dict[str, Any] | None = None,
        session_context: str = "",
    ) -> str:
        """操作を記録し、operation_id を返す。"""
        operation_id = str(uuid.uuid4())
        entry = {
            "operation_id": operation_id,
            "timestamp": _now_jst(),
            "operation": operation,
            "target_path": target_path,
            "actor": actor,
            "session_context": session_context,
            "success": success,
            "error": error,
            "details": details or {},
        }

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        data = _load_log(self.log_path, self.museum_id)
        data.setdefault("operations", []).append(entry)

        from core.storage import atomic_write

        yaml = YAML()
        stream = StringIO()
        yaml.dump(data, stream)
        atomic_write(self.log_path, stream.getvalue())

        return operation_id
