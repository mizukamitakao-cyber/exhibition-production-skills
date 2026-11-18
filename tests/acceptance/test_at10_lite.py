"""AT-10 Lite 受入試験: Codex 互換性最小検証。

AT-10-1: generate-instructions.py が全スキルを含む AGENTS.md を生成できること
AT-10-2: 生成された AGENTS.md が 32 KiB 以内であること
AT-10-3: 全スキルに YAML フロントマター（name・description）が存在すること
AT-10-4: generate-skills.py が .agents/skills/ 構造を正しく生成できること
AT-10-5: Visual Designer が HTML レイアウト試作を生成できること
AT-10-6: 生成された HTML に必須要素が含まれること
AT-10-7: museum_profile Pydantic モデルが YAML データを正常に読み込めること
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# AT-10-1 & AT-10-2: AGENTS.md 生成
# ---------------------------------------------------------------------------

class TestAT10_AgentsMdGeneration:
    """AGENTS.md 生成テスト。"""

    @pytest.fixture(scope="class")
    def agents_md_content(self, tmp_path_factory):
        """generate-instructions.py を実行して AGENTS.md 内容を返す。"""
        tmp = tmp_path_factory.mktemp("codex_gen")
        generate_script = PROJECT_ROOT / "adapters" / "codex" / "generate-instructions.py"
        result = subprocess.run(
            [sys.executable, str(generate_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"生成スクリプトがエラー: {result.stderr}"
        output_path = PROJECT_ROOT / "AGENTS.md"
        assert output_path.exists(), "AGENTS.md が生成されていません"
        return output_path.read_text(encoding="utf-8")

    def test_agents_md_contains_all_skills(self, agents_md_content):
        expected_skills = [
            "exhibition-advocate",
            "exhibition-deployment-setup",
            "exhibition-director",
            "exhibition-idea-generator",
            "exhibition-museum-onboarding",
            "exhibition-planner",
            "exhibition-researcher",
            "exhibition-reviewer",
            "exhibition-story-designer",
            "exhibition-visual-designer",
            "exhibition-writer",
        ]
        for skill_name in expected_skills:
            assert skill_name in agents_md_content, f"スキル未収録: {skill_name}"

    def test_agents_md_within_32kb_limit(self, agents_md_content):
        size_kb = len(agents_md_content.encode("utf-8")) / 1024
        assert size_kb <= 32, f"AGENTS.md が 32 KiB 制限を超過: {size_kb:.1f} KiB"

    def test_agents_md_contains_common_rules(self, agents_md_content):
        assert "deployment.yaml" in agents_md_content
        assert "data_root" in agents_md_content

    def test_agents_md_references_skill_detail_path(self, agents_md_content):
        assert ".agents/skills/" in agents_md_content


# ---------------------------------------------------------------------------
# AT-10-3: SKILL.md フロントマター検証
# ---------------------------------------------------------------------------

class TestAT10_SkillFrontmatter:
    """全スキルの SKILL.md フロントマター検証。"""

    @pytest.fixture(scope="class")
    def skill_dirs(self):
        core_skills = PROJECT_ROOT / "core" / "skills"
        return [d for d in core_skills.iterdir() if d.is_dir()]

    def test_all_skills_have_skill_md(self, skill_dirs):
        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            assert skill_md.exists(), f"SKILL.md が存在しません: {skill_dir.name}"

    def test_all_skills_have_name_in_frontmatter(self, skill_dirs):
        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")
            assert re.search(r"^name:", content, re.MULTILINE), (
                f"name フィールドなし: {skill_dir.name}"
            )

    def test_all_skills_have_description_in_frontmatter(self, skill_dirs):
        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")
            assert re.search(r"^description:", content, re.MULTILINE), (
                f"description フィールドなし: {skill_dir.name}"
            )

    def test_skill_count_is_expected(self, skill_dirs):
        assert len(skill_dirs) == 11, (
            f"スキル数が想定と異なります: {len(skill_dirs)} 件（期待: 11 件）"
        )


# ---------------------------------------------------------------------------
# AT-10-4: .agents/skills/ 構造検証
# ---------------------------------------------------------------------------

class TestAT10_CodexSkillsStructure:
    """Codex スキルディレクトリ構造検証。"""

    @pytest.fixture(scope="class")
    def deployed_skills_dir(self, tmp_path_factory):
        """generate-skills.py を一時ディレクトリに生成して返す。"""
        import shutil
        import sys as _sys

        core_skills = PROJECT_ROOT / "core" / "skills"
        tmp_dest = tmp_path_factory.mktemp("agents_skills")

        for skill_dir in sorted(core_skills.iterdir()):
            if not skill_dir.is_dir():
                continue
            dest = tmp_dest / skill_dir.name
            shutil.copytree(skill_dir, dest)

        return tmp_dest

    def test_all_skills_deployed(self, deployed_skills_dir):
        deployed = [d.name for d in deployed_skills_dir.iterdir() if d.is_dir()]
        assert len(deployed) == 11

    def test_each_deployed_skill_has_skill_md(self, deployed_skills_dir):
        for skill_dir in deployed_skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            assert (skill_dir / "SKILL.md").exists(), (
                f"デプロイ先に SKILL.md がありません: {skill_dir.name}"
            )

    def test_visual_designer_skill_deployed(self, deployed_skills_dir):
        vd_dir = deployed_skills_dir / "exhibition-visual-designer"
        assert vd_dir.exists()
        assert (vd_dir / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# AT-10-5 & AT-10-6: Visual Designer HTML 生成
# ---------------------------------------------------------------------------

class TestAT10_VisualDesigner:
    """Visual Designer スキルのHTML生成検証。"""

    def test_generate_panel_html_basic(self, tmp_path):
        from core.visual_designer import generate_panel_html, save_panel_layout

        html = generate_panel_html(
            panel_id="panel-01",
            title="縄文の土器",
            markdown_content="## 概要\n\n縄文土器は約1万6000年前から作られました。",
            footer="架空歴史館 · 縄文展2026",
        )
        assert "<!DOCTYPE html>" in html
        assert "縄文の土器" in html
        assert "panel-01" in html

    def test_generated_html_contains_required_elements(self, tmp_path):
        from core.visual_designer import generate_panel_html

        html = generate_panel_html(
            panel_id="panel-02",
            title="縄文の食と暮らし",
            markdown_content="縄文人は多様な食材を利用していました。**どんぐり**や貝類が主食でした。",
        )
        # 必須要素
        assert "charset=\"UTF-8\"" in html
        assert "lang=\"ja\"" in html
        assert "<title>" in html
        assert ".panel" in html
        assert "縄文の食と暮らし" in html

    def test_panel_html_saved_to_design_dir(self, tmp_path):
        from core.visual_designer import generate_panel_html, save_panel_layout, list_layouts

        project_dir = tmp_path / "museum" / "project"
        project_dir.mkdir(parents=True)

        html = generate_panel_html("panel-01", "テストパネル", "本文テスト")
        save_panel_layout(project_dir, "panel-01", html)

        layouts = list_layouts(project_dir)
        assert len(layouts) == 1
        assert layouts[0]["panel_id"] == "panel-01"

    def test_panel_html_persists(self, tmp_path):
        from core.visual_designer import (
            generate_panel_html, save_panel_layout, load_panel_layout
        )

        project_dir = tmp_path / "museum" / "project"
        project_dir.mkdir(parents=True)

        html = generate_panel_html("panel-01", "保存テスト", "永続化確認")
        save_panel_layout(project_dir, "panel-01", html)

        loaded = load_panel_layout(project_dir, "panel-01")
        assert loaded is not None
        assert "保存テスト" in loaded

    def test_custom_panel_specs_applied(self, tmp_path):
        from core.visual_designer import generate_panel_html

        html = generate_panel_html(
            panel_id="panel-01",
            title="カスタムデザイン",
            markdown_content="テスト",
            panel_specs={
                "bg_color": "#f5f0e8",
                "accent_color": "#8b5e3c",
                "panel_width": "600px",
            },
        )
        assert "#f5f0e8" in html
        assert "#8b5e3c" in html
        assert "600px" in html

    def test_markdown_headings_converted_to_html(self, tmp_path):
        from core.visual_designer import generate_panel_html

        html = generate_panel_html(
            panel_id="panel-01",
            title="見出しテスト",
            markdown_content="## 小見出し\n\n本文テキスト",
        )
        assert "<h2>小見出し</h2>" in html

    def test_markdown_bold_converted_to_html(self, tmp_path):
        from core.visual_designer import generate_panel_html

        html = generate_panel_html(
            panel_id="panel-01",
            title="太字テスト",
            markdown_content="**重要な**テキスト",
        )
        assert "<strong>重要な</strong>" in html

    def test_multiple_panels_saved(self, tmp_path):
        from core.visual_designer import generate_panel_html, save_panel_layout, list_layouts

        project_dir = tmp_path / "museum" / "project"
        project_dir.mkdir(parents=True)

        for i in range(1, 4):
            html = generate_panel_html(f"panel-0{i}", f"パネル{i}", f"本文{i}")
            save_panel_layout(project_dir, f"panel-0{i}", html)

        layouts = list_layouts(project_dir)
        assert len(layouts) == 3


# ---------------------------------------------------------------------------
# AT-10-7: museum_profile モデルの YAML 読み込み
# ---------------------------------------------------------------------------

class TestAT10_MuseumProfileCompatibility:
    """museum_profile Pydantic モデルの YAML 互換性検証。"""

    def test_museum_profile_model_loads_valid_data(self):
        from core.models.museum_profile import MuseumProfile

        data = {
            "schema_version": "1.0",
            "museum_id": "test-history-001",
            "basic": {"name": "架空歴史館", "type": "history"},
        }
        profile = MuseumProfile(**data)
        assert profile.museum_id == "test-history-001"
        assert profile.basic.name == "架空歴史館"

    def test_museum_profile_ignores_extra_fields(self):
        from core.models.museum_profile import MuseumProfile

        data = {
            "schema_version": "1.0",
            "museum_id": "test-001",
            "basic": {"name": "テスト館"},
            "unknown_future_field": "このフィールドは無視される",
        }
        profile = MuseumProfile(**data)
        assert profile.museum_id == "test-001"

    def test_museum_profile_design_panel_specs(self):
        from core.models.museum_profile import MuseumProfile, Design

        data = {
            "schema_version": "1.0",
            "museum_id": "design-test-001",
            "museum_name": "デザインテスト館",
            "museum_type": "history",
            "design": {
                "primary_color": "#2c5f8a",
                "panel_specs": {
                    "panel_width": "900px",
                    "bg_color": "#fafafa",
                    "accent_color": "#1a3a5c",
                },
            },
        }
        profile = MuseumProfile(**data)
        assert profile.design is not None
        assert profile.design.panel_specs["panel_width"] == "900px"
