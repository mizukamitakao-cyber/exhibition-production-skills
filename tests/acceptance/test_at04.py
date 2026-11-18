"""AT-04 受入試験: 出典管理テスト。

AT-04-1: 架空の出典作成要求を拒否できること（ルールの検証）
AT-04-2: 調査メモに事実を記録し、出典を紐付けできること
AT-04-3: 出典のない重要事実は unverified として記録されること
"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.models.source_registry import Source
from core.researcher import (
    ResearchError,
    add_source,
    create_source_registry,
    get_unverified_sources,
    load_registry,
    mark_verified,
    record_usage,
    save_registry,
    save_research_memo,
    update_source,
)
from core.models.artifact_manifest import Artifact
from core.planner import (
    add_artifact,
    create_artifact_manifest,
    get_artifact,
    load_artifact_manifest,
    register_plan_artifact,
    save_artifact_manifest,
    save_plan_draft,
    update_artifact_status,
)


MUSEUM_ID = "test-history-museum-001"
PROJECT_ID = "test-project-at04"


def _create_project_dir(tmp_path: Path) -> Path:
    project_dir = tmp_path / MUSEUM_ID / PROJECT_ID
    project_dir.mkdir(parents=True)
    return project_dir


class TestAT04_1_NoFakeSources:
    """AT-04-1: 架空出典の作成が拒否されること。

    注意: 出典誠実性ルール自体はスキル（SKILL.md）レベルで実施される。
    このテストは Python レイヤーでのルール整合性を確認する:
    - 出典は必ず source_id・title・type を持つ（空の出典は登録できない設計にはなっていないが、
      verification_status="unverified" がデフォルトで記録される）
    - 重複した source_id は登録できない（架空出典の上書きリスクを防ぐ）
    """

    def test_source_has_verification_status_field(self):
        src = Source(
            source_id="src-001",
            type="academic",
            title="架空の書籍",
            verification_status="unverified",
        )
        assert src.verification_status == "unverified"

    def test_cannot_register_duplicate_source_id(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        add_source(reg, Source(
            source_id="src-001",
            type="academic",
            title="既存の出典",
            verification_status="verified",
        ))
        with pytest.raises(ResearchError, match="重複"):
            add_source(reg, Source(
                source_id="src-001",
                type="web",
                title="架空の出典（同一ID）",
                verification_status="verified",
            ))

    def test_new_source_defaults_to_unverified(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        src = Source(source_id="src-001", type="academic", title="テスト出典")
        add_source(reg, src)
        assert reg.sources[0].verification_status in ("unverified", "")

    def test_verified_source_requires_explicit_mark(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        src = Source(source_id="src-001", type="academic", title="出典")
        add_source(reg, src)
        assert reg.sources[0].verification_status != "verified"
        mark_verified(reg, "src-001")
        assert reg.sources[0].verification_status == "verified"


class TestAT04_2_SourceUsageTracking:
    """AT-04-2: 調査メモに事実を記録し出典を紐付けできること。"""

    def test_save_research_memo(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        content = """# 調査メモ 001：縄文時代の食と暮らし

## 確認済み事実

縄文時代（約16000年前〜約3000年前）は日本の先史時代である。【src-001】

## 研究上の解釈

縄文人は豊かな動植物を食料として利用していたと考えられている。【src-002】

## 未確認事項

- [ ] 縄文土器の種類と地域差（要調査）
"""
        path = save_research_memo(project_dir, "001", content)
        assert path.exists()
        saved = path.read_text(encoding="utf-8")
        assert "確認済み事実" in saved
        assert "未確認事項" in saved

    def test_link_source_to_artifact(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        add_source(reg, Source(
            source_id="src-001",
            type="academic",
            title="縄文時代の考古学的研究",
            author="山田太郎",
            year=2020,
            verification_status="unverified",
        ))
        record_usage(reg, "src-001", "plan-v1", "第1章")
        save_registry(reg, project_dir)

        loaded = load_registry(project_dir)
        assert loaded is not None
        assert len(loaded.source_usage) == 1
        assert loaded.source_usage[0].source_id == "src-001"
        assert "plan-v1" in loaded.source_usage[0].used_in_artifacts

    def test_multiple_sources_for_one_artifact(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        for i in range(3):
            add_source(reg, Source(
                source_id=f"src-00{i + 1}",
                type="academic",
                title=f"出典{i + 1}",
                verification_status="unverified",
            ))
        for i in range(3):
            record_usage(reg, f"src-00{i + 1}", "plan-v1", f"第{i + 1}章")
        save_registry(reg, project_dir)

        loaded = load_registry(project_dir)
        assert loaded is not None
        assert len(loaded.source_usage) == 3
        for usage in loaded.source_usage:
            assert "plan-v1" in usage.used_in_artifacts


class TestAT04_3_UnverifiedTracking:
    """AT-04-3: 未確認事実は unverified として記録されること。"""

    def test_unverified_sources_are_listed(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        add_source(reg, Source(
            source_id="src-001",
            type="academic",
            title="確認済み出典",
            verification_status="verified",
        ))
        add_source(reg, Source(
            source_id="src-002",
            type="web",
            title="未確認出典",
            verification_status="unverified",
        ))
        unverified = get_unverified_sources(reg)
        assert len(unverified) == 1
        assert unverified[0].source_id == "src-002"

    def test_verified_source_not_in_unverified_list(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        add_source(reg, Source(
            source_id="src-001",
            type="academic",
            title="テスト出典",
            verification_status="unverified",
        ))
        mark_verified(reg, "src-001")
        unverified = get_unverified_sources(reg)
        assert len(unverified) == 0

    def test_unverified_persisted_after_save_load(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        add_source(reg, Source(
            source_id="src-001",
            type="web",
            title="未確認出典",
            verification_status="unverified",
        ))
        save_registry(reg, project_dir)

        loaded = load_registry(project_dir)
        assert loaded is not None
        unverified = get_unverified_sources(loaded)
        assert len(unverified) == 1
        assert unverified[0].verification_status == "unverified"

    def test_all_sources_can_be_verified(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        reg = create_source_registry(PROJECT_ID)
        for i in range(3):
            add_source(reg, Source(
                source_id=f"src-00{i + 1}",
                type="academic",
                title=f"出典{i + 1}",
                verification_status="unverified",
            ))
        for i in range(3):
            mark_verified(reg, f"src-00{i + 1}")
        save_registry(reg, project_dir)

        loaded = load_registry(project_dir)
        assert loaded is not None
        unverified = get_unverified_sources(loaded)
        assert len(unverified) == 0


class TestAT04_PlanIntegration:
    """AT-04 統合: 出典台帳と企画書の連携。"""

    def test_plan_created_and_artifact_registered(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        content = "# 企画書 v1\n\n## 目的\nテスト企画書"
        save_plan_draft(project_dir, content, version=1)

        manifest = create_artifact_manifest(PROJECT_ID)
        register_plan_artifact(manifest, project_dir, version=1, title="テスト企画書")
        save_artifact_manifest(manifest, project_dir)

        loaded = load_artifact_manifest(project_dir)
        assert loaded is not None
        artifact = get_artifact(loaded, "plan-v1")
        assert artifact is not None
        assert artifact.status == "draft"

    def test_plan_approval_flow(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        save_plan_draft(project_dir, "# 企画書 v1", version=1)
        manifest = create_artifact_manifest(PROJECT_ID)
        register_plan_artifact(manifest, project_dir, version=1)
        update_artifact_status(manifest, "plan-v1", "approved")
        save_artifact_manifest(manifest, project_dir)

        loaded = load_artifact_manifest(project_dir)
        assert loaded is not None
        artifact = get_artifact(loaded, "plan-v1")
        assert artifact is not None
        assert artifact.status == "approved"
        assert artifact.approved_at is not None
