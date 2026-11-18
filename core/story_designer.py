"""
展示構成表管理。
Exhibition Story Designer スキルのPythonサポート。
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.models.story_structure import StorySection, StoryStructure
from core.yaml_io import load_yaml, save_yaml


class StoryError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_story_structure(project_id: str, version: int = 1) -> StoryStructure:
    now = _now_iso()
    return StoryStructure(
        project_id=project_id,
        version=version,
        created_at=now,
        updated_at=now,
    )


def add_section(structure: StoryStructure, section: StorySection) -> StoryStructure:
    existing_ids = {s.section_id for s in structure.sections}
    if section.section_id in existing_ids:
        raise StoryError(f"セクションIDが重複しています: {section.section_id}")
    if section.display_order == 0:
        section.display_order = len(structure.sections) + 1
    structure.sections.append(section)
    structure.updated_at = _now_iso()
    return structure


def update_section(
    structure: StoryStructure,
    section_id: str,
    **updates: object,
) -> StoryStructure:
    section = next((s for s in structure.sections if s.section_id == section_id), None)
    if section is None:
        raise StoryError(f"セクションが見つかりません: {section_id}")
    for key, value in updates.items():
        if hasattr(section, key):
            setattr(section, key, value)
    structure.updated_at = _now_iso()
    return structure


def reorder_sections(structure: StoryStructure, ordered_ids: list[str]) -> StoryStructure:
    """ordered_ids の順序に従って display_order を再割り当てする。"""
    id_set = {s.section_id for s in structure.sections}
    for sid in ordered_ids:
        if sid not in id_set:
            raise StoryError(f"セクションが見つかりません: {sid}")
    for i, sid in enumerate(ordered_ids, start=1):
        section = next(s for s in structure.sections if s.section_id == sid)
        section.display_order = i
    structure.sections.sort(key=lambda s: s.display_order)
    structure.updated_at = _now_iso()
    return structure


def set_story_status(
    structure: StoryStructure,
    status: str,
) -> StoryStructure:
    structure.status = status  # type: ignore[assignment]
    structure.updated_at = _now_iso()
    return structure


def get_story_dir(project_dir: Path) -> Path:
    return project_dir / "story"


def _story_filename(version: int) -> str:
    return f"story-structure-v{version}.yaml"


def save_story_structure(structure: StoryStructure, project_dir: Path) -> None:
    story_dir = get_story_dir(project_dir)
    story_dir.mkdir(exist_ok=True)
    save_yaml(story_dir / _story_filename(structure.version), structure)


def load_story_structure(
    project_dir: Path,
    version: int | None = None,
) -> StoryStructure | None:
    story_dir = get_story_dir(project_dir)
    if version is None:
        version = _get_latest_version(story_dir)
    if version == 0:
        return None
    path = story_dir / _story_filename(version)
    if not path.exists():
        return None
    return load_yaml(path, StoryStructure)


def _get_latest_version(story_dir: Path) -> int:
    if not story_dir.exists():
        return 0
    best = 0
    for f in story_dir.glob("story-structure-v*.yaml"):
        try:
            v = int(f.stem.split("-v")[1])
            if v > best:
                best = v
        except (IndexError, ValueError):
            pass
    return best


def build_structure_md(structure: StoryStructure) -> str:
    """構成表を Markdown 形式で出力する。"""
    status_label = {
        "draft": "下書き",
        "ready_for_review": "レビュー待ち",
        "approved": "✓ 承認済み",
    }
    sections_sorted = sorted(structure.sections, key=lambda s: s.display_order)
    lines = [
        f"# 展示構成表 v{structure.version} — {structure.project_id}",
        "",
        f"ステータス：{status_label.get(structure.status, structure.status)}",
        "",
        "## 全体ストーリー",
        "",
        structure.overall_narrative or "（未記載）",
        "",
        "---",
        "",
    ]
    for sec in sections_sorted:
        lines += [
            f"## {sec.display_order}. {sec.title}（`{sec.section_id}`）",
            "",
        ]
        if sec.narrative:
            lines += [f"**ストーリー：** {sec.narrative}", ""]
        if sec.key_messages:
            lines += ["**主要メッセージ：**"] + [f"- {m}" for m in sec.key_messages] + [""]
        if sec.exhibit_items:
            lines += ["**展示資料：**"] + [f"- {item}" for item in sec.exhibit_items] + [""]
        if sec.panel_count:
            lines += [f"**パネル枚数目安：** {sec.panel_count}", ""]
        lines += ["---", ""]
    return "\n".join(lines)
