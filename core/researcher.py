"""
出典管理。
Exhibition Researcher スキルのPythonサポート。

出典誠実性ルール（上書き不可）：
- 架空の出典・引用を作成しない
- 確認済み事実・研究上の解釈・AI推論を区別して記録する
- 出典不明の事実は「未確認」として扱う
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.models.source_registry import Source, SourceRegistry, SourceUsage
from core.yaml_io import load_yaml, save_yaml


class ResearchError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_source_registry(project_id: str) -> SourceRegistry:
    return SourceRegistry(project_id=project_id, updated_at=_now_iso())


def add_source(registry: SourceRegistry, source: Source) -> SourceRegistry:
    existing_ids = {s.source_id for s in registry.sources}
    if source.source_id in existing_ids:
        raise ResearchError(f"出典IDが重複しています: {source.source_id}")
    registry.sources.append(source)
    registry.updated_at = _now_iso()
    return registry


def update_source(registry: SourceRegistry, source_id: str, **updates: object) -> SourceRegistry:
    source = next((s for s in registry.sources if s.source_id == source_id), None)
    if source is None:
        raise ResearchError(f"出典が見つかりません: {source_id}")
    for key, value in updates.items():
        if hasattr(source, key):
            setattr(source, key, value)
    registry.updated_at = _now_iso()
    return registry


def mark_verified(registry: SourceRegistry, source_id: str) -> SourceRegistry:
    return update_source(registry, source_id, verification_status="verified")


def mark_unverified(registry: SourceRegistry, source_id: str) -> SourceRegistry:
    return update_source(registry, source_id, verification_status="unverified")


def get_unverified_sources(registry: SourceRegistry) -> list[Source]:
    return [
        s for s in registry.sources
        if s.verification_status in ("unverified", "")
    ]


def record_usage(
    registry: SourceRegistry,
    source_id: str,
    artifact_id: str,
    sections: str = "",
) -> SourceRegistry:
    usage = next((u for u in registry.source_usage if u.source_id == source_id), None)
    if usage is None:
        usage = SourceUsage(source_id=source_id)
        registry.source_usage.append(usage)
    if artifact_id not in usage.used_in_artifacts:
        usage.used_in_artifacts.append(artifact_id)
    if sections:
        usage.sections = sections
    registry.updated_at = _now_iso()
    return registry


def get_research_dir(project_dir: Path) -> Path:
    return project_dir / "research"


def save_registry(registry: SourceRegistry, project_dir: Path) -> None:
    research_dir = get_research_dir(project_dir)
    research_dir.mkdir(exist_ok=True)
    save_yaml(research_dir / "source-registry.yaml", registry)


def load_registry(project_dir: Path) -> SourceRegistry | None:
    path = get_research_dir(project_dir) / "source-registry.yaml"
    if not path.exists():
        return None
    return load_yaml(path, SourceRegistry)


def save_research_memo(project_dir: Path, memo_id: str, content: str) -> Path:
    """調査メモを research/memo-{memo_id}.md として保存する。"""
    from core.storage import atomic_write
    research_dir = get_research_dir(project_dir)
    research_dir.mkdir(exist_ok=True)
    path = research_dir / f"memo-{memo_id}.md"
    atomic_write(path, content)
    return path


def load_research_memo(project_dir: Path, memo_id: str) -> str | None:
    path = get_research_dir(project_dir) / f"memo-{memo_id}.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
