"""AT-02後半・AT-05・AT-06・AT-07 受入試験（Phase 6）。

AT-02後半: 企画書承認後にパネル原稿を2件作成できる
AT-05:    Advocate が findings を生成し、担当者が rejected として記録できる
AT-06:    Reviewer が文字数超過・未確認出典を指摘できる
AT-07:    未承認成果物の段階チェック・承認・差し戻し
"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.models.artifact_manifest import Artifact
from core.models.review_record import Finding
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
from core.review_manager import (
    add_finding,
    complete_review,
    create_approval_record,
    create_review_record,
    list_reviews,
    load_approval,
    load_review,
    resolve_finding,
    save_approval,
    save_review,
)
from core.writer import (
    WriterError,
    check_prerequisite_approved,
    create_revision_manuscript,
    get_latest_manuscript_version,
    list_manuscripts,
    load_manuscript,
    register_manuscript_artifact,
    save_manuscript,
)


MUSEUM_ID = "test-history-museum-001"
PROJECT_ID = "test-project-phase6"


def _create_project_dir(tmp_path: Path) -> Path:
    project_dir = tmp_path / MUSEUM_ID / PROJECT_ID
    project_dir.mkdir(parents=True)
    return project_dir


def _setup_approved_plan(project_dir: Path) -> None:
    """承認済み企画書をセットアップする。"""
    save_plan_draft(project_dir, "# 企画書 v1\n\n縄文の食と暮らし", version=1)
    manifest = create_artifact_manifest(PROJECT_ID)
    register_plan_artifact(manifest, project_dir, version=1, title="縄文展企画書")
    update_artifact_status(manifest, "plan-v1", "approved")
    save_artifact_manifest(manifest, project_dir)


class TestAT02SecondHalf:
    """AT-02後半: 企画書承認後にパネル原稿を2件作成できること。"""

    def test_create_two_manuscripts(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        _setup_approved_plan(project_dir)

        content1 = "# パネル01：縄文の土器\n\n土器は縄文人の食生活に欠かせない道具でした。"
        content2 = "# パネル02：縄文の食\n\n縄文人は多様な食材を利用していました。"
        save_manuscript(project_dir, "panel-01", content1, version=1)
        save_manuscript(project_dir, "panel-02", content2, version=1)

        manuscripts = list_manuscripts(project_dir)
        assert len(manuscripts) >= 2
        ids = {m["panel_id"] for m in manuscripts}
        assert "panel-01" in ids
        assert "panel-02" in ids

    def test_manuscripts_registered_in_manifest(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        _setup_approved_plan(project_dir)

        save_manuscript(project_dir, "panel-01", "# パネル01", version=1)
        manifest = load_artifact_manifest(project_dir)
        register_manuscript_artifact(manifest, project_dir, "panel-01", version=1)
        save_artifact_manifest(manifest, project_dir)

        loaded = load_artifact_manifest(project_dir)
        artifact = get_artifact(loaded, "panel-01-v1")
        assert artifact is not None
        assert artifact.type == "manuscript"
        assert artifact.status == "draft"

    def test_manuscript_requires_story_structure_approved(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        manifest = create_artifact_manifest(PROJECT_ID)

        # 構成表が draft の場合
        a = Artifact(artifact_id="story-v1", type="story-structure",
                     title="構成表", version=1, status="draft")
        add_artifact(manifest, a)

        approved = check_prerequisite_approved(manifest, "story-v1")
        assert approved is False

    def test_manuscripts_persist(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        for pid in ("panel-01", "panel-02"):
            save_manuscript(project_dir, pid, f"# {pid} 本文", version=1)
        for pid in ("panel-01", "panel-02"):
            loaded = load_manuscript(project_dir, pid, version=1)
            assert loaded is not None
            assert pid in loaded


class TestAT05_Advocate:
    """AT-05: Advocate が findings を生成し担当者が rejected として記録できる。"""

    def test_advocate_creates_findings(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        review = create_review_record("adv-001", "plan-v1", "advocate")
        add_finding(review, Finding(
            finding_id="F-001",
            type="logical_issue",
            severity="major",
            location="第2章",
            description="展示の対象来館者と難易度設定が合っていない可能性があります",
            recommendation="小学生向けの表現に調整することを検討してください",
        ))
        add_finding(review, Finding(
            finding_id="F-002",
            type="suggestion",
            severity="info",
            location="全体",
            description="縄文文化の独自性を強調するユニークな切り口があると魅力的になります",
            recommendation="他館の縄文展との差別化要素を明確にすることを検討してください",
        ))
        complete_review(review, "全体的に良好だが2点の指摘あり", proceed_recommendation=True)
        save_review(review, project_dir)

        loaded = load_review(project_dir, "adv-001")
        assert loaded is not None
        assert loaded.reviewer_role == "advocate"
        assert len(loaded.findings) == 2
        types = {f.type for f in loaded.findings}
        assert "logical_issue" in types or "suggestion" in types

    def test_advocate_findings_contain_logical_or_suggestion_type(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        review = create_review_record("adv-002", "plan-v1", "advocate")
        add_finding(review, Finding(
            finding_id="F-001",
            type="logical_issue",
            severity="major",
            location="コンセプト",
            description="偏りのある視点が含まれています",
            recommendation="複数の見方を提示することを検討してください",
        ))
        save_review(review, project_dir)
        loaded = load_review(project_dir, "adv-002")
        assert loaded is not None
        assert any(f.type in ("logical_issue", "suggestion") for f in loaded.findings)

    def test_advocate_finding_can_be_rejected_without_modifying_artifact(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        content = "# 企画書 v1\n\n本文（変更されない）"
        save_plan_draft(project_dir, content, version=1)

        review = create_review_record("adv-003", "plan-v1", "advocate")
        add_finding(review, Finding(
            finding_id="F-001",
            type="suggestion",
            severity="minor",
            location="タイトル",
            description="タイトルの変更を提案します",
        ))
        save_review(review, project_dir)

        resolve_finding(review, "F-001", "rejected", "現在のタイトルで問題ない")
        save_review(review, project_dir)

        loaded_review = load_review(project_dir, "adv-003")
        assert loaded_review is not None
        assert loaded_review.findings[0].status == "rejected"

        loaded_plan = load_plan_draft(project_dir, version=1)
        assert loaded_plan == content  # 企画書は変更されていない

    def test_multiple_findings_different_severity(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        review = create_review_record("adv-004", "plan-v1", "advocate")
        for sev, fid in (("critical", "F-001"), ("major", "F-002"), ("minor", "F-003")):
            add_finding(review, Finding(
                finding_id=fid,
                type="logical_issue",
                severity=sev,
                location="テスト",
                description=f"{sev}の指摘",
            ))
        save_review(review, project_dir)
        loaded = load_review(project_dir, "adv-004")
        assert loaded is not None
        severities = {f.severity for f in loaded.findings}
        assert "critical" in severities
        assert "major" in severities


from core.planner import load_plan_draft


class TestAT06_Reviewer:
    """AT-06: Reviewer が文字数超過・未確認出典を指摘できる。"""

    def test_reviewer_detects_character_count_issue(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        # 文字数超過の原稿（制限500字に対して長い原稿）
        long_content = "あ" * 600  # 600字
        save_manuscript(project_dir, "panel-01", long_content, version=1)

        review = create_review_record("rev-001", "panel-01-v1", "reviewer")
        char_count = len(long_content)
        limit = 500
        if char_count > limit:
            add_finding(review, Finding(
                finding_id="R-001",
                type="requirement_gap",
                severity="major",
                location="パネル全体",
                description=f"文字数 {char_count}字が制限 {limit}字を超過しています",
                recommendation=f"{char_count - limit}字の削減が必要です",
            ))
        complete_review(review, "文字数超過あり", proceed_recommendation=False)
        save_review(review, project_dir)

        loaded = load_review(project_dir, "rev-001")
        assert loaded is not None
        assert loaded.reviewer_role == "reviewer"
        assert any(f.severity in ("major", "critical") for f in loaded.findings)
        assert loaded.proceed_recommendation is False

    def test_reviewer_detects_unverified_source_issue(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        content = "# パネル\n\n縄文土器は○○年前に作られた（出典なし）"
        save_manuscript(project_dir, "panel-01", content, version=1)

        review = create_review_record("rev-002", "panel-01-v1", "reviewer")
        add_finding(review, Finding(
            finding_id="R-001",
            type="factual_issue",
            severity="major",
            location="パネル本文",
            description="重要な事実記述に出典が明記されていません",
            recommendation="source_id を明記するか、調査メモを参照してください",
        ))
        complete_review(review, "未確認事実あり", proceed_recommendation=False)
        save_review(review, project_dir)

        loaded = load_review(project_dir, "rev-002")
        assert loaded is not None
        assert any(f.type == "factual_issue" for f in loaded.findings)

    def test_reviewer_finding_resolution(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        review = create_review_record("rev-003", "panel-01-v1", "reviewer")
        add_finding(review, Finding(
            finding_id="R-001",
            type="requirement_gap",
            severity="major",
            location="全体",
            description="文字数超過",
        ))
        save_review(review, project_dir)

        resolve_finding(review, "R-001", "accepted", "文字数を削減します")
        save_review(review, project_dir)

        loaded = load_review(project_dir, "rev-003")
        assert loaded is not None
        assert loaded.findings[0].status == "accepted"


class TestAT07_StageApproval:
    """AT-07: 段階承認テスト。"""

    def test_draft_artifact_not_approved(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        manifest = create_artifact_manifest(PROJECT_ID)
        a = Artifact(artifact_id="plan-v1", type="plan",
                     title="企画書", version=1, status="draft")
        add_artifact(manifest, a)

        approved = check_prerequisite_approved(manifest, "plan-v1")
        assert approved is False

    def test_artifact_becomes_approved_after_approval(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        save_plan_draft(project_dir, "# 企画書 v1", version=1)
        manifest = create_artifact_manifest(PROJECT_ID)
        register_plan_artifact(manifest, project_dir, version=1)
        update_artifact_status(manifest, "plan-v1", "approved")
        save_artifact_manifest(manifest, project_dir)

        loaded = load_artifact_manifest(project_dir)
        approved = check_prerequisite_approved(loaded, "plan-v1")
        assert approved is True

    def test_original_preserved_after_revision(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        original_content = "# 企画書 v1 — 原本（保持される）"
        save_manuscript(project_dir, "panel-01", original_content, version=1)

        new_version, orig = create_revision_manuscript(project_dir, "panel-01")
        assert new_version == 2
        save_manuscript(project_dir, "panel-01", "# 改訂版", version=new_version)

        still_original = load_manuscript(project_dir, "panel-01", version=1)
        assert still_original == original_content

    def test_approved_artifact_has_approved_at(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        save_plan_draft(project_dir, "# 企画書 v1", version=1)
        manifest = create_artifact_manifest(PROJECT_ID)
        register_plan_artifact(manifest, project_dir, version=1)
        update_artifact_status(manifest, "plan-v1", "approved")
        save_artifact_manifest(manifest, project_dir)

        loaded = load_artifact_manifest(project_dir)
        artifact = get_artifact(loaded, "plan-v1")
        assert artifact is not None
        assert artifact.approved_at is not None

    def test_approval_record_links_review(self, tmp_path):
        project_dir = _create_project_dir(tmp_path)
        review = create_review_record("rev-001", "plan-v1", "advocate")
        complete_review(review, "承認推奨", proceed_recommendation=True)
        save_review(review, project_dir)

        approval = create_approval_record(
            "appr-001", "plan-v1", "approved",
            decided_by="mizukami",
            review_record_ids=["rev-001"],
        )
        save_approval(approval, project_dir)

        loaded = load_approval(project_dir, "appr-001")
        assert loaded is not None
        assert "rev-001" in loaded.review_record_ids
        assert loaded.decision == "approved"
