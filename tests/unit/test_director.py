"""core/director.py のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.director import (
    advance_project_phase,
    create_project,
    get_latest_approved_profile_path,
    get_project_dir,
    list_projects,
    load_project,
    save_project,
)
from core.models.exhibition_project import ExhibitionProject


def test_create_project_defaults():
    p = create_project("proj-01", "museum-001")
    assert p.project_id == "proj-01"
    assert p.museum_id == "museum-001"
    assert p.status == "planning"
    assert p.current_phase == "idea"
    assert p.completed_phases == []


def test_create_project_with_title():
    p = create_project("proj-02", "museum-001", title="縄文の食と暮らし")
    assert p.title == "縄文の食と暮らし"


def test_create_project_profile_version():
    p = create_project("proj-03", "museum-001", profile_version=3)
    assert p.profile_version == 3


def test_save_and_load_project(tmp_path):
    project = create_project("proj-save", "museum-001", title="テスト展示")
    path = tmp_path / "exhibition-project.yaml"
    save_project(project, path)
    loaded = load_project(path)
    assert loaded.project_id == "proj-save"
    assert loaded.title == "テスト展示"
    assert loaded.status == "planning"


def test_save_project_updates_updated_at(tmp_path):
    project = create_project("proj-ts", "museum-001")
    path = tmp_path / "exhibition-project.yaml"
    old_ts = project.updated_at
    import time; time.sleep(0.01)
    save_project(project, path)
    loaded = load_project(path)
    assert loaded.updated_at >= old_ts


def test_get_project_dir(tmp_path):
    d = get_project_dir(tmp_path, "proj-abc")
    assert d == tmp_path / "proj-abc"


def test_list_projects_empty(tmp_path):
    result = list_projects(tmp_path)
    assert result == []


def test_list_projects_nonexistent(tmp_path):
    result = list_projects(tmp_path / "no-such-dir")
    assert result == []


def test_list_projects_finds_yaml(tmp_path):
    for pid in ("proj-b", "proj-a"):
        d = tmp_path / pid
        d.mkdir()
        project = create_project(pid, "museum-001")
        save_project(project, d / "exhibition-project.yaml")
    result = list_projects(tmp_path)
    assert len(result) == 2
    ids = [p.parent.name for p in result]
    assert "proj-a" in ids
    assert "proj-b" in ids


def test_list_projects_ignores_non_project_dirs(tmp_path):
    (tmp_path / "not-a-project").mkdir()
    d = tmp_path / "real-proj"
    d.mkdir()
    project = create_project("real-proj", "museum-001")
    save_project(project, d / "exhibition-project.yaml")
    result = list_projects(tmp_path)
    assert len(result) == 1


def test_get_latest_approved_profile_path_none(tmp_path):
    result = get_latest_approved_profile_path(tmp_path)
    assert result is None


def test_get_latest_approved_profile_path_single(tmp_path):
    p = tmp_path / "museum-profile-v1.yaml"
    p.write_text("museum_id: museum-001\n")
    result = get_latest_approved_profile_path(tmp_path)
    assert result == p


def test_get_latest_approved_profile_path_multiple(tmp_path):
    for v in (1, 2, 3):
        (tmp_path / f"museum-profile-v{v}.yaml").write_text(f"museum_id: museum-001\n")
    result = get_latest_approved_profile_path(tmp_path)
    assert result == tmp_path / "museum-profile-v3.yaml"


def test_advance_project_phase_moves_phase(tmp_path):
    project = create_project("proj-adv", "museum-001")
    assert project.current_phase == "idea"
    advance_project_phase(project, "content")
    assert project.current_phase == "content"
    assert "idea" in project.completed_phases


def test_advance_project_phase_accumulates(tmp_path):
    project = create_project("proj-chain", "museum-001")
    advance_project_phase(project, "content")
    advance_project_phase(project, "design")
    assert project.current_phase == "design"
    assert "idea" in project.completed_phases
    assert "content" in project.completed_phases


def test_advance_project_phase_no_duplicate(tmp_path):
    project = create_project("proj-dup", "museum-001")
    advance_project_phase(project, "content")
    advance_project_phase(project, "content")  # 同フェーズに戻す場合
    assert project.completed_phases.count("idea") == 1
