"""AT-02 受入試験（前半）: 新規展示制作テスト — アイディア生成・選定。

AT-02-1: test-history-museum-001 でアイディア創出を実行する
AT-02-2: 3件以上のアイディアが追加できる
AT-02-3: 1件を選択する
"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.director import (
    create_project,
    get_latest_approved_profile_path,
    save_project,
)
from core.ideas import (
    IdeaError,
    add_idea,
    create_idea_list,
    load_idea_list,
    reject_idea,
    save_idea_list,
    select_idea,
)
from core.models.idea_list import IdeaEntry


MUSEUM_ID = "test-history-museum-001"
PROJECT_ID = "test-project-at02"


def _create_test_environment(tmp_path: Path) -> tuple[Path, Path]:
    """テスト用館ディレクトリとプロジェクトディレクトリを作成する。"""
    museum_dir = tmp_path / MUSEUM_ID
    museum_dir.mkdir()
    # 承認済みプロファイルのダミーファイルを作成
    (museum_dir / "museum-profile-v1.yaml").write_text(
        "museum_id: test-history-museum-001\ndomain: history\n",
        encoding="utf-8",
    )
    project_dir = museum_dir / PROJECT_ID
    project_dir.mkdir()
    project = create_project(
        project_id=PROJECT_ID,
        museum_id=MUSEUM_ID,
        title="縄文時代の食と暮らし",
        profile_version=1,
    )
    project.brief.theme = "縄文人の日常生活を体験的に学ぶ"
    project.brief.target_visitors = ["小学生", "家族連れ"]
    project.brief.period = "2027年4月〜7月"
    save_project(project, project_dir / "exhibition-project.yaml")
    return museum_dir, project_dir


def _make_idea(idea_id: str, title: str) -> IdeaEntry:
    return IdeaEntry(
        id=idea_id,
        title=title,
        concept=f"{title}のコンセプト説明",
        key_themes=["縄文", "体験", "生活"],
        unique_points=["インタラクティブ展示", "地域素材使用"],
        target_visitors=["小学生", "家族連れ"],
        estimated_duration="60分",
    )


class TestAT02_1_IdeaListCreation:
    """AT-02-1: アイディアリストが作成できること。"""

    def test_create_idea_list_for_project(self, tmp_path):
        museum_dir, project_dir = _create_test_environment(tmp_path)
        il = create_idea_list(PROJECT_ID, MUSEUM_ID, "縄文の体験展示")
        save_idea_list(il, project_dir)
        loaded = load_idea_list(project_dir)
        assert loaded is not None
        assert loaded.project_id == PROJECT_ID
        assert loaded.museum_id == MUSEUM_ID

    def test_museum_has_approved_profile(self, tmp_path):
        museum_dir, _ = _create_test_environment(tmp_path)
        profile = get_latest_approved_profile_path(museum_dir)
        assert profile is not None
        assert "v1" in profile.name

    def test_project_exists(self, tmp_path):
        _, project_dir = _create_test_environment(tmp_path)
        assert (project_dir / "exhibition-project.yaml").exists()


class TestAT02_2_IdeaGeneration:
    """AT-02-2: 3件以上のアイディアが追加できること。"""

    def test_add_three_or_more_ideas(self, tmp_path):
        _, project_dir = _create_test_environment(tmp_path)
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        ideas = [
            _make_idea("idea-01", "縄文クッキング体験"),
            _make_idea("idea-02", "土器づくりの旅"),
            _make_idea("idea-03", "縄文の森へようこそ"),
        ]
        for entry in ideas:
            add_idea(il, entry)
        save_idea_list(il, project_dir)

        loaded = load_idea_list(project_dir)
        assert loaded is not None
        assert len(loaded.ideas) >= 3

    def test_all_ideas_start_as_proposed(self, tmp_path):
        _, project_dir = _create_test_environment(tmp_path)
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        for i in range(3):
            add_idea(il, _make_idea(f"idea-0{i + 1}", f"案{i + 1}"))
        for entry in il.ideas:
            assert entry.status == "proposed"

    def test_ideas_have_required_fields(self, tmp_path):
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        entry = _make_idea("idea-01", "縄文クッキング体験")
        add_idea(il, entry)
        idea = il.ideas[0]
        assert idea.title != ""
        assert idea.concept != ""
        assert len(idea.key_themes) > 0
        assert len(idea.unique_points) > 0
        assert len(idea.target_visitors) > 0
        assert idea.estimated_duration != ""

    def test_duplicate_idea_id_rejected(self, tmp_path):
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        add_idea(il, _make_idea("idea-01", "案1"))
        with pytest.raises(IdeaError):
            add_idea(il, _make_idea("idea-01", "重複案"))

    def test_comparison_md_generated_on_save(self, tmp_path):
        from core.ideas import save_comparison_md
        _, project_dir = _create_test_environment(tmp_path)
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        for i in range(3):
            add_idea(il, _make_idea(f"idea-0{i + 1}", f"案{i + 1}"))
        save_comparison_md(il, project_dir)
        md_path = project_dir / "ideas" / "comparison.md"
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        for i in range(3):
            assert f"案{i + 1}" in content


class TestAT02_3_IdeaSelection:
    """AT-02-3: 1件を選択できること。"""

    def test_select_one_idea(self, tmp_path):
        _, project_dir = _create_test_environment(tmp_path)
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        for i in range(3):
            add_idea(il, _make_idea(f"idea-0{i + 1}", f"案{i + 1}"))
        select_idea(il, "idea-02")
        assert il.selected_idea_id == "idea-02"
        selected = next(e for e in il.ideas if e.id == "idea-02")
        assert selected.status == "selected"

    def test_other_ideas_remain_proposed_after_selection(self, tmp_path):
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        for i in range(3):
            add_idea(il, _make_idea(f"idea-0{i + 1}", f"案{i + 1}"))
        select_idea(il, "idea-02")
        for entry in il.ideas:
            if entry.id != "idea-02":
                assert entry.status == "proposed"

    def test_re_select_different_idea(self, tmp_path):
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        for i in range(3):
            add_idea(il, _make_idea(f"idea-0{i + 1}", f"案{i + 1}"))
        select_idea(il, "idea-01")
        select_idea(il, "idea-03")
        assert il.selected_idea_id == "idea-03"
        idea1 = next(e for e in il.ideas if e.id == "idea-01")
        assert idea1.status == "proposed"

    def test_selection_persisted_after_save_load(self, tmp_path):
        _, project_dir = _create_test_environment(tmp_path)
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        for i in range(3):
            add_idea(il, _make_idea(f"idea-0{i + 1}", f"案{i + 1}"))
        select_idea(il, "idea-02")
        save_idea_list(il, project_dir)

        loaded = load_idea_list(project_dir)
        assert loaded is not None
        assert loaded.selected_idea_id == "idea-02"
        selected = next(e for e in loaded.ideas if e.id == "idea-02")
        assert selected.status == "selected"

    def test_cannot_select_rejected_idea(self, tmp_path):
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        add_idea(il, _make_idea("idea-01", "却下予定案"))
        reject_idea(il, "idea-01", "方向性が違う")
        with pytest.raises(IdeaError):
            select_idea(il, "idea-01")

    def test_cannot_reject_selected_idea(self, tmp_path):
        il = create_idea_list(PROJECT_ID, MUSEUM_ID)
        add_idea(il, _make_idea("idea-01", "選定済み案"))
        select_idea(il, "idea-01")
        with pytest.raises(IdeaError):
            reject_idea(il, "idea-01")
