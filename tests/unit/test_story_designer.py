"""core/story_designer.py のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.models.story_structure import StorySection
from core.story_designer import (
    StoryError,
    add_section,
    build_structure_md,
    create_story_structure,
    load_story_structure,
    reorder_sections,
    save_story_structure,
    set_story_status,
    update_section,
)


def _make_section(section_id: str, title: str = "テストセクション", order: int = 0) -> StorySection:
    return StorySection(
        section_id=section_id,
        title=title,
        narrative="セクション説明",
        display_order=order,
    )


def test_create_story_structure():
    structure = create_story_structure("proj-01")
    assert structure.project_id == "proj-01"
    assert structure.version == 1
    assert structure.status == "draft"
    assert structure.sections == []


def test_create_story_structure_version():
    structure = create_story_structure("proj-01", version=2)
    assert structure.version == 2


def test_add_section():
    structure = create_story_structure("proj-01")
    add_section(structure, _make_section("sec-01"))
    assert len(structure.sections) == 1


def test_add_section_auto_order():
    structure = create_story_structure("proj-01")
    add_section(structure, _make_section("sec-01"))
    add_section(structure, _make_section("sec-02"))
    assert structure.sections[0].display_order == 1
    assert structure.sections[1].display_order == 2


def test_add_section_duplicate_raises():
    structure = create_story_structure("proj-01")
    add_section(structure, _make_section("sec-01"))
    with pytest.raises(StoryError, match="重複"):
        add_section(structure, _make_section("sec-01"))


def test_update_section():
    structure = create_story_structure("proj-01")
    add_section(structure, _make_section("sec-01"))
    update_section(structure, "sec-01", title="更新後タイトル")
    assert structure.sections[0].title == "更新後タイトル"


def test_update_section_not_found_raises():
    structure = create_story_structure("proj-01")
    with pytest.raises(StoryError, match="見つかりません"):
        update_section(structure, "no-such", title="x")


def test_reorder_sections():
    structure = create_story_structure("proj-01")
    for i, sid in enumerate(("sec-01", "sec-02", "sec-03"), start=1):
        add_section(structure, _make_section(sid, order=i))
    reorder_sections(structure, ["sec-03", "sec-01", "sec-02"])
    orders = {s.section_id: s.display_order for s in structure.sections}
    assert orders["sec-03"] == 1
    assert orders["sec-01"] == 2
    assert orders["sec-02"] == 3


def test_reorder_sections_sorts_list():
    structure = create_story_structure("proj-01")
    for sid in ("sec-01", "sec-02", "sec-03"):
        add_section(structure, _make_section(sid))
    reorder_sections(structure, ["sec-03", "sec-01", "sec-02"])
    assert structure.sections[0].section_id == "sec-03"
    assert structure.sections[1].section_id == "sec-01"
    assert structure.sections[2].section_id == "sec-02"


def test_reorder_sections_unknown_id_raises():
    structure = create_story_structure("proj-01")
    add_section(structure, _make_section("sec-01"))
    with pytest.raises(StoryError, match="見つかりません"):
        reorder_sections(structure, ["sec-01", "no-such"])


def test_set_story_status():
    structure = create_story_structure("proj-01")
    set_story_status(structure, "approved")
    assert structure.status == "approved"


def test_save_and_load_story_structure(tmp_path):
    structure = create_story_structure("proj-io", version=1)
    add_section(structure, _make_section("sec-01", "保存テストセクション"))
    save_story_structure(structure, tmp_path)
    loaded = load_story_structure(tmp_path, version=1)
    assert loaded is not None
    assert loaded.project_id == "proj-io"
    assert len(loaded.sections) == 1
    assert loaded.sections[0].title == "保存テストセクション"


def test_load_story_structure_latest(tmp_path):
    for v in (1, 2):
        structure = create_story_structure("proj-latest", version=v)
        save_story_structure(structure, tmp_path)
    loaded = load_story_structure(tmp_path)
    assert loaded is not None
    assert loaded.version == 2


def test_load_story_structure_missing_returns_none(tmp_path):
    result = load_story_structure(tmp_path)
    assert result is None


def test_build_structure_md_contains_titles():
    structure = create_story_structure("proj-01")
    structure.overall_narrative = "縄文から現代への旅"
    add_section(structure, StorySection(
        section_id="sec-01",
        title="縄文の生活",
        narrative="土器づくりと食の文化",
        key_messages=["縄文人は豊かな自然の中で生きていた"],
        panel_count=3,
        display_order=1,
    ))
    md = build_structure_md(structure)
    assert "縄文の生活" in md
    assert "縄文から現代への旅" in md
    assert "縄文人は豊かな自然の中で生きていた" in md


def test_build_structure_md_shows_status():
    structure = create_story_structure("proj-01")
    set_story_status(structure, "approved")
    md = build_structure_md(structure)
    assert "承認済み" in md
