"""
アイディア管理。
Idea Generator スキルのPythonサポート。
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.models.idea_list import IdeaEntry, IdeaList
from core.storage import atomic_write
from core.yaml_io import load_yaml, save_yaml


class IdeaError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_idea_list(
    project_id: str,
    museum_id: str,
    brief_summary: str = "",
) -> IdeaList:
    now = _now_iso()
    return IdeaList(
        project_id=project_id,
        museum_id=museum_id,
        brief_summary=brief_summary,
        generated_at=now,
        updated_at=now,
    )


def add_idea(idea_list: IdeaList, entry: IdeaEntry) -> IdeaList:
    existing_ids = {i.id for i in idea_list.ideas}
    if entry.id in existing_ids:
        raise IdeaError(f"アイディアIDが重複しています: {entry.id}")
    idea_list.ideas.append(entry)
    idea_list.updated_at = _now_iso()
    return idea_list


def select_idea(idea_list: IdeaList, idea_id: str) -> IdeaList:
    idea = next((i for i in idea_list.ideas if i.id == idea_id), None)
    if not idea:
        raise IdeaError(f"アイディアが見つかりません: {idea_id}")
    if idea.status == "rejected":
        raise IdeaError(f"却下済みのアイディアは選定できません: {idea_id}")

    for i in idea_list.ideas:
        if i.status == "selected":
            i.status = "proposed"
            i.selected_at = None

    idea.status = "selected"
    idea.selected_at = _now_iso()
    idea_list.selected_idea_id = idea_id
    idea_list.updated_at = _now_iso()
    return idea_list


def reject_idea(idea_list: IdeaList, idea_id: str, reason: str = "") -> IdeaList:
    idea = next((i for i in idea_list.ideas if i.id == idea_id), None)
    if not idea:
        raise IdeaError(f"アイディアが見つかりません: {idea_id}")
    if idea.status == "selected":
        raise IdeaError("選定済みのアイディアは却下できません。先に別のアイディアを選定してください。")
    idea.status = "rejected"
    idea.rejection_reason = reason
    idea_list.updated_at = _now_iso()
    return idea_list


def build_comparison_md(idea_list: IdeaList) -> str:
    """アイディア比較表を Markdown 形式で生成する。"""
    status_label = {"proposed": "候補", "selected": "✓ **選定**", "rejected": "✗ 却下"}
    lines = [
        f"# アイディア比較表 — {idea_list.project_id}",
        "",
        f"生成日時：{idea_list.generated_at[:10]}  ",
        f"案件ID：`{idea_list.project_id}`  ",
        "",
        "---",
        "",
    ]
    for idea in idea_list.ideas:
        label = status_label.get(idea.status, idea.status)
        lines += [f"## {idea.title}（`{idea.id}`）　{label}", ""]
        lines += [f"**コンセプト：** {idea.concept}", ""]
        if idea.key_themes:
            lines += ["**主要テーマ：**"] + [f"- {t}" for t in idea.key_themes] + [""]
        if idea.unique_points:
            lines += ["**ユニークポイント：**"] + [f"- {p}" for p in idea.unique_points] + [""]
        if idea.target_visitors:
            lines += [f"**対象来館者：** {', '.join(idea.target_visitors)}", ""]
        if idea.estimated_duration:
            lines += [f"**所要時間目安：** {idea.estimated_duration}", ""]
        if idea.rejection_reason:
            lines += [f"**却下理由：** {idea.rejection_reason}", ""]
        lines += ["---", ""]

    if idea_list.selected_idea_id:
        selected = next((i for i in idea_list.ideas if i.id == idea_list.selected_idea_id), None)
        if selected:
            date = (selected.selected_at or "")[:10]
            lines += [
                "## 選定結果",
                "",
                f"**採用アイディア：** {selected.title}（`{date}` 選定）",
                "",
            ]
    return "\n".join(lines)


def get_ideas_dir(project_dir: Path) -> Path:
    return project_dir / "ideas"


def save_idea_list(idea_list: IdeaList, project_dir: Path) -> None:
    ideas_dir = get_ideas_dir(project_dir)
    ideas_dir.mkdir(exist_ok=True)
    save_yaml(ideas_dir / "idea-list.yaml", idea_list)


def load_idea_list(project_dir: Path) -> IdeaList | None:
    path = get_ideas_dir(project_dir) / "idea-list.yaml"
    if not path.exists():
        return None
    return load_yaml(path, IdeaList)


def save_comparison_md(idea_list: IdeaList, project_dir: Path) -> None:
    ideas_dir = get_ideas_dir(project_dir)
    ideas_dir.mkdir(exist_ok=True)
    atomic_write(ideas_dir / "comparison.md", build_comparison_md(idea_list))
