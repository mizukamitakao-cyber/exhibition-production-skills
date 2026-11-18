"""
レビュー・承認管理。
Exhibition Advocate・Reviewer スキルのPythonサポート。
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.models.approval_record import ApprovalRecord
from core.models.review_record import Finding, ReviewRecord
from core.yaml_io import load_yaml, save_yaml


class ReviewError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── ReviewRecord ──────────────────────────────────────────────────────

def create_review_record(
    review_id: str,
    artifact_id: str,
    reviewer_role: str,
) -> ReviewRecord:
    return ReviewRecord(
        review_id=review_id,
        artifact_id=artifact_id,
        reviewer_role=reviewer_role,  # type: ignore[arg-type]
        reviewed_at=_now_iso(),
    )


def add_finding(review: ReviewRecord, finding: Finding) -> ReviewRecord:
    existing_ids = {f.finding_id for f in review.findings}
    if finding.finding_id in existing_ids:
        raise ReviewError(f"指摘IDが重複しています: {finding.finding_id}")
    review.findings.append(finding)
    return review


def resolve_finding(
    review: ReviewRecord,
    finding_id: str,
    status: str,
    note: str = "",
) -> ReviewRecord:
    finding = next((f for f in review.findings if f.finding_id == finding_id), None)
    if finding is None:
        raise ReviewError(f"指摘が見つかりません: {finding_id}")
    finding.status = status  # type: ignore[assignment]
    if note:
        finding.resolution_note = note
    finding.resolved_at = _now_iso()
    return review


def complete_review(
    review: ReviewRecord,
    overall_assessment: str,
    proceed_recommendation: bool | None = None,
) -> ReviewRecord:
    review.overall_assessment = overall_assessment
    review.proceed_recommendation = proceed_recommendation
    return review


def get_reviews_dir(project_dir: Path) -> Path:
    return project_dir / "reviews"


def save_review(review: ReviewRecord, project_dir: Path) -> None:
    reviews_dir = get_reviews_dir(project_dir)
    reviews_dir.mkdir(exist_ok=True)
    save_yaml(reviews_dir / f"review-{review.review_id}.yaml", review)


def load_review(project_dir: Path, review_id: str) -> ReviewRecord | None:
    path = get_reviews_dir(project_dir) / f"review-{review_id}.yaml"
    if not path.exists():
        return None
    return load_yaml(path, ReviewRecord)


def list_reviews(
    project_dir: Path,
    artifact_id: str | None = None,
) -> list[ReviewRecord]:
    reviews_dir = get_reviews_dir(project_dir)
    if not reviews_dir.exists():
        return []
    result = []
    for f in sorted(reviews_dir.glob("review-*.yaml")):
        review = load_yaml(f, ReviewRecord)
        if artifact_id is None or review.artifact_id == artifact_id:
            result.append(review)
    return result


# ── ApprovalRecord ────────────────────────────────────────────────────

def create_approval_record(
    approval_id: str,
    artifact_id: str,
    decision: str,
    decided_by: str = "",
    review_record_ids: list[str] | None = None,
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        artifact_id=artifact_id,
        decision=decision,  # type: ignore[arg-type]
        decided_at=_now_iso(),
        decided_by=decided_by,
        review_record_ids=review_record_ids or [],
    )


def save_approval(approval: ApprovalRecord, project_dir: Path) -> None:
    reviews_dir = get_reviews_dir(project_dir)
    reviews_dir.mkdir(exist_ok=True)
    save_yaml(reviews_dir / f"approval-{approval.approval_id}.yaml", approval)


def load_approval(project_dir: Path, approval_id: str) -> ApprovalRecord | None:
    path = get_reviews_dir(project_dir) / f"approval-{approval_id}.yaml"
    if not path.exists():
        return None
    return load_yaml(path, ApprovalRecord)


def list_approvals(
    project_dir: Path,
    artifact_id: str | None = None,
) -> list[ApprovalRecord]:
    reviews_dir = get_reviews_dir(project_dir)
    if not reviews_dir.exists():
        return []
    result = []
    for f in sorted(reviews_dir.glob("approval-*.yaml")):
        approval = load_yaml(f, ApprovalRecord)
        if artifact_id is None or approval.artifact_id == artifact_id:
            result.append(approval)
    return result
