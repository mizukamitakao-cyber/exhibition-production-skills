"""core/review_manager.py のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.models.review_record import Finding
from core.review_manager import (
    ReviewError,
    add_finding,
    complete_review,
    create_approval_record,
    create_review_record,
    list_approvals,
    list_reviews,
    load_approval,
    load_review,
    resolve_finding,
    save_approval,
    save_review,
)


def _make_finding(finding_id: str, severity: str = "minor") -> Finding:
    return Finding(
        finding_id=finding_id,
        type="logical_issue",
        severity=severity,
        location="第1章",
        description="テスト指摘",
        recommendation="改善案",
    )


def test_create_review_record():
    review = create_review_record("rev-001", "plan-v1", "advocate")
    assert review.review_id == "rev-001"
    assert review.artifact_id == "plan-v1"
    assert review.reviewer_role == "advocate"
    assert review.findings == []


def test_add_finding():
    review = create_review_record("rev-001", "plan-v1", "advocate")
    add_finding(review, _make_finding("F-001"))
    assert len(review.findings) == 1
    assert review.findings[0].finding_id == "F-001"


def test_add_finding_duplicate_raises():
    review = create_review_record("rev-001", "plan-v1", "advocate")
    add_finding(review, _make_finding("F-001"))
    with pytest.raises(ReviewError, match="重複"):
        add_finding(review, _make_finding("F-001"))


def test_resolve_finding_accepted():
    review = create_review_record("rev-001", "plan-v1", "advocate")
    add_finding(review, _make_finding("F-001"))
    resolve_finding(review, "F-001", "accepted", "修正します")
    f = review.findings[0]
    assert f.status == "accepted"
    assert f.resolution_note == "修正します"
    assert f.resolved_at is not None


def test_resolve_finding_rejected():
    review = create_review_record("rev-001", "plan-v1", "advocate")
    add_finding(review, _make_finding("F-001"))
    resolve_finding(review, "F-001", "rejected")
    assert review.findings[0].status == "rejected"


def test_resolve_finding_not_found_raises():
    review = create_review_record("rev-001", "plan-v1", "advocate")
    with pytest.raises(ReviewError, match="見つかりません"):
        resolve_finding(review, "no-such", "accepted")


def test_complete_review():
    review = create_review_record("rev-001", "plan-v1", "advocate")
    complete_review(review, "全体的に良好です", proceed_recommendation=True)
    assert review.overall_assessment == "全体的に良好です"
    assert review.proceed_recommendation is True


def test_complete_review_no_proceed():
    review = create_review_record("rev-001", "plan-v1", "reviewer")
    complete_review(review, "要修正あり", proceed_recommendation=False)
    assert review.proceed_recommendation is False


def test_save_and_load_review(tmp_path):
    review = create_review_record("rev-001", "plan-v1", "advocate")
    add_finding(review, _make_finding("F-001"))
    complete_review(review, "良好")
    save_review(review, tmp_path)
    loaded = load_review(tmp_path, "rev-001")
    assert loaded is not None
    assert loaded.review_id == "rev-001"
    assert len(loaded.findings) == 1


def test_load_review_missing_returns_none(tmp_path):
    result = load_review(tmp_path, "no-such-review")
    assert result is None


def test_list_reviews(tmp_path):
    for i in range(3):
        review = create_review_record(f"rev-00{i + 1}", "plan-v1", "advocate")
        save_review(review, tmp_path)
    result = list_reviews(tmp_path)
    assert len(result) == 3


def test_list_reviews_filter_by_artifact(tmp_path):
    r1 = create_review_record("rev-001", "plan-v1", "advocate")
    r2 = create_review_record("rev-002", "panel-01-v1", "reviewer")
    save_review(r1, tmp_path)
    save_review(r2, tmp_path)
    result = list_reviews(tmp_path, artifact_id="plan-v1")
    assert len(result) == 1
    assert result[0].artifact_id == "plan-v1"


def test_create_approval_record():
    approval = create_approval_record("appr-001", "plan-v1", "approved", "mizukami")
    assert approval.approval_id == "appr-001"
    assert approval.artifact_id == "plan-v1"
    assert approval.decision == "approved"
    assert approval.decided_by == "mizukami"


def test_save_and_load_approval(tmp_path):
    approval = create_approval_record("appr-001", "plan-v1", "approved", "mizukami")
    save_approval(approval, tmp_path)
    loaded = load_approval(tmp_path, "appr-001")
    assert loaded is not None
    assert loaded.approval_id == "appr-001"
    assert loaded.decision == "approved"


def test_load_approval_missing_returns_none(tmp_path):
    result = load_approval(tmp_path, "no-such-approval")
    assert result is None


def test_list_approvals(tmp_path):
    for i in range(2):
        a = create_approval_record(f"appr-00{i + 1}", "plan-v1", "approved")
        save_approval(a, tmp_path)
    result = list_approvals(tmp_path)
    assert len(result) == 2


def test_approval_with_review_ids(tmp_path):
    approval = create_approval_record(
        "appr-001", "plan-v1", "approved",
        review_record_ids=["rev-001", "rev-002"],
    )
    save_approval(approval, tmp_path)
    loaded = load_approval(tmp_path, "appr-001")
    assert loaded is not None
    assert "rev-001" in loaded.review_record_ids
