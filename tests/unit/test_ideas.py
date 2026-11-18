"""core/ideas.py のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.ideas import (
    IdeaError,
    add_idea,
    build_comparison_md,
    create_idea_list,
    get_ideas_dir,
    load_idea_list,
    reject_idea,
    save_comparison_md,
    save_idea_list,
    select_idea,
)
from core.models.idea_list import IdeaEntry, IdeaList


def _make_entry(idea_id: str, title: str = "テスト案") -> IdeaEntry:
    return IdeaEntry(id=idea_id, title=title, concept="テスト用コンセプト")


def test_create_idea_list():
    il = create_idea_list("proj-01", "museum-001", "テストブリーフ")
    assert il.project_id == "proj-01"
    assert il.museum_id == "museum-001"
    assert il.brief_summary == "テストブリーフ"
    assert il.ideas == []
    assert il.selected_idea_id is None


def test_add_idea():
    il = create_idea_list("proj-01", "museum-001")
    entry = _make_entry("idea-01")
    add_idea(il, entry)
    assert len(il.ideas) == 1
    assert il.ideas[0].id == "idea-01"


def test_add_idea_duplicate_raises():
    il = create_idea_list("proj-01", "museum-001")
    add_idea(il, _make_entry("idea-01"))
    with pytest.raises(IdeaError, match="重複"):
        add_idea(il, _make_entry("idea-01"))


def test_add_idea_updates_updated_at():
    il = create_idea_list("proj-01", "museum-001")
    old_ts = il.updated_at
    import time; time.sleep(0.01)
    add_idea(il, _make_entry("idea-01"))
    assert il.updated_at >= old_ts


def test_select_idea():
    il = create_idea_list("proj-01", "museum-001")
    add_idea(il, _make_entry("idea-01"))
    select_idea(il, "idea-01")
    assert il.selected_idea_id == "idea-01"
    assert il.ideas[0].status == "selected"
    assert il.ideas[0].selected_at is not None


def test_select_idea_clears_previous_selection():
    il = create_idea_list("proj-01", "museum-001")
    add_idea(il, _make_entry("idea-01"))
    add_idea(il, _make_entry("idea-02"))
    select_idea(il, "idea-01")
    select_idea(il, "idea-02")
    assert il.selected_idea_id == "idea-02"
    idea1 = next(i for i in il.ideas if i.id == "idea-01")
    assert idea1.status == "proposed"
    assert idea1.selected_at is None


def test_select_idea_not_found_raises():
    il = create_idea_list("proj-01", "museum-001")
    with pytest.raises(IdeaError, match="見つかりません"):
        select_idea(il, "no-such-idea")


def test_select_rejected_idea_raises():
    il = create_idea_list("proj-01", "museum-001")
    add_idea(il, _make_entry("idea-01"))
    reject_idea(il, "idea-01", "方向性が違う")
    with pytest.raises(IdeaError, match="却下済み"):
        select_idea(il, "idea-01")


def test_reject_idea():
    il = create_idea_list("proj-01", "museum-001")
    add_idea(il, _make_entry("idea-01"))
    reject_idea(il, "idea-01", "コスト超過")
    assert il.ideas[0].status == "rejected"
    assert il.ideas[0].rejection_reason == "コスト超過"


def test_reject_selected_idea_raises():
    il = create_idea_list("proj-01", "museum-001")
    add_idea(il, _make_entry("idea-01"))
    select_idea(il, "idea-01")
    with pytest.raises(IdeaError, match="選定済み"):
        reject_idea(il, "idea-01")


def test_reject_idea_not_found_raises():
    il = create_idea_list("proj-01", "museum-001")
    with pytest.raises(IdeaError, match="見つかりません"):
        reject_idea(il, "no-such-idea")


def test_build_comparison_md_contains_titles():
    il = create_idea_list("proj-01", "museum-001")
    add_idea(il, IdeaEntry(
        id="idea-01",
        title="縄文の食と暮らし",
        concept="縄文人の日常を体験",
        key_themes=["食", "生活"],
        unique_points=["体験型"],
    ))
    md = build_comparison_md(il)
    assert "縄文の食と暮らし" in md
    assert "idea-01" in md
    assert "体験型" in md


def test_build_comparison_md_shows_selected():
    il = create_idea_list("proj-proj-sel", "museum-001")
    add_idea(il, _make_entry("idea-01", "採用案"))
    select_idea(il, "idea-01")
    md = build_comparison_md(il)
    assert "採用案" in md
    assert "選定結果" in md


def test_build_comparison_md_shows_rejected():
    il = create_idea_list("proj-proj-rej", "museum-001")
    add_idea(il, _make_entry("idea-01", "却下案"))
    reject_idea(il, "idea-01", "方向性が違う")
    md = build_comparison_md(il)
    assert "方向性が違う" in md


def test_save_and_load_idea_list(tmp_path):
    il = create_idea_list("proj-io", "museum-001", "ブリーフ")
    add_idea(il, _make_entry("idea-01", "保存テスト案"))
    save_idea_list(il, tmp_path)
    loaded = load_idea_list(tmp_path)
    assert loaded is not None
    assert loaded.project_id == "proj-io"
    assert len(loaded.ideas) == 1
    assert loaded.ideas[0].title == "保存テスト案"


def test_load_idea_list_missing_returns_none(tmp_path):
    result = load_idea_list(tmp_path)
    assert result is None


def test_get_ideas_dir(tmp_path):
    d = get_ideas_dir(tmp_path)
    assert d == tmp_path / "ideas"


def test_save_comparison_md_creates_file(tmp_path):
    il = create_idea_list("proj-md", "museum-001")
    add_idea(il, _make_entry("idea-01", "MD保存テスト"))
    save_comparison_md(il, tmp_path)
    md_path = tmp_path / "ideas" / "comparison.md"
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "MD保存テスト" in content
