"""
展示プロジェクト管理。
Exhibition Director スキルのPythonサポート。
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.models.exhibition_project import ExhibitionProject
from core.yaml_io import load_yaml, save_yaml


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_project(
    project_id: str,
    museum_id: str,
    title: str = "",
    profile_version: int = 1,
    type_: str = "new",
) -> ExhibitionProject:
    """新しい展示プロジェクトを作成する（in_memory）。"""
    now = _now_iso()
    return ExhibitionProject(
        project_id=project_id,
        museum_id=museum_id,
        profile_version=profile_version,
        title=title,
        type=type_,
        status="planning",
        created_at=now,
        updated_at=now,
        current_phase="idea",
    )


def load_project(project_path: Path) -> ExhibitionProject:
    """exhibition-project.yaml を読み込む。"""
    return load_yaml(project_path, ExhibitionProject)


def save_project(project: ExhibitionProject, project_path: Path) -> None:
    """exhibition-project.yaml をアトミックに保存する。"""
    project.updated_at = _now_iso()
    save_yaml(project_path, project)


def get_project_dir(museum_dir: Path, project_id: str) -> Path:
    return museum_dir / project_id


def list_projects(museum_dir: Path) -> list[Path]:
    """museum_dir内の全プロジェクトの exhibition-project.yaml パスを返す。"""
    result = []
    if not museum_dir.exists():
        return result
    for item in sorted(museum_dir.iterdir()):
        if item.is_dir():
            project_file = item / "exhibition-project.yaml"
            if project_file.exists():
                result.append(project_file)
    return result


def get_latest_approved_profile_path(museum_dir: Path) -> Path | None:
    """最新の承認済みプロファイルのパスを返す。見つからなければ None。"""
    best_version = 0
    best_path = None
    for f in museum_dir.glob("museum-profile-v*.yaml"):
        try:
            v = int(f.stem.split("-v")[1])
            if v > best_version:
                best_version = v
                best_path = f
        except (IndexError, ValueError):
            pass
    return best_path


def advance_project_phase(project: ExhibitionProject, new_phase: str) -> ExhibitionProject:
    """プロジェクトのフェーズを進める。"""
    if project.current_phase and project.current_phase not in project.completed_phases:
        project.completed_phases.append(project.current_phase)
    project.current_phase = new_phase
    project.updated_at = _now_iso()
    return project
