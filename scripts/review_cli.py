#!/usr/bin/env python3
"""
レビュー・承認管理CLI。
exhibition-advocate / exhibition-reviewer スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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


def cmd_create_review(args: argparse.Namespace) -> None:
    review = create_review_record(args.review_id, args.artifact_id, args.reviewer_role)
    project_dir = Path(args.project_dir)
    save_review(review, project_dir)
    print(json.dumps({
        "status": "created",
        "review_id": review.review_id,
        "artifact_id": review.artifact_id,
        "reviewer_role": review.reviewer_role,
    }))


def cmd_add_finding(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    review = load_review(project_dir, args.review_id)
    if review is None:
        print(json.dumps({"status": "error", "message": "レビューが見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        import json as _json
        finding_data = _json.loads(args.finding_json)
        finding = Finding(**finding_data)
        add_finding(review, finding)
    except ReviewError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_review(review, project_dir)
    print(json.dumps({
        "status": "added",
        "finding_id": finding.finding_id,
        "total_findings": len(review.findings),
    }))


def cmd_resolve_finding(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    review = load_review(project_dir, args.review_id)
    if review is None:
        print(json.dumps({"status": "error", "message": "レビューが見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        resolve_finding(review, args.finding_id, args.resolution, args.note or "")
    except ReviewError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_review(review, project_dir)
    print(json.dumps({"status": "resolved", "finding_id": args.finding_id, "resolution": args.resolution}))


def cmd_complete_review(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    review = load_review(project_dir, args.review_id)
    if review is None:
        print(json.dumps({"status": "error", "message": "レビューが見つかりません"}), file=sys.stderr)
        sys.exit(1)

    proceed = None
    if args.proceed is not None:
        proceed = args.proceed.lower() == "true"
    complete_review(review, args.assessment, proceed)
    save_review(review, project_dir)
    print(json.dumps({
        "status": "completed",
        "review_id": review.review_id,
        "finding_count": len(review.findings),
        "proceed_recommendation": review.proceed_recommendation,
    }))


def cmd_create_approval(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    review_ids = []
    if args.review_ids:
        review_ids = [r.strip() for r in args.review_ids.split(",") if r.strip()]
    approval = create_approval_record(
        args.approval_id,
        args.artifact_id,
        args.decision,
        args.decided_by or "",
        review_ids,
    )
    if args.conditions:
        approval.conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    if args.rejection_reason:
        approval.rejection_reason = args.rejection_reason
    save_approval(approval, project_dir)
    print(json.dumps({
        "status": "created",
        "approval_id": approval.approval_id,
        "decision": approval.decision,
    }))


def cmd_review_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    reviews = list_reviews(project_dir, args.artifact_id or None)
    approvals = list_approvals(project_dir, args.artifact_id or None)
    print(json.dumps({
        "review_count": len(reviews),
        "reviews": [
            {
                "review_id": r.review_id,
                "artifact_id": r.artifact_id,
                "reviewer_role": r.reviewer_role,
                "finding_count": len(r.findings),
                "proceed_recommendation": r.proceed_recommendation,
            }
            for r in reviews
        ],
        "approval_count": len(approvals),
        "approvals": [
            {
                "approval_id": a.approval_id,
                "artifact_id": a.artifact_id,
                "decision": a.decision,
                "decided_at": a.decided_at,
            }
            for a in approvals
        ],
    }))


def main() -> None:
    parser = argparse.ArgumentParser(prog="review_cli", description="レビュー・承認管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-review", help="レビューレコードを作成する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--review-id", required=True)
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--reviewer-role", required=True, choices=["advocate", "reviewer"])

    p = sub.add_parser("add-finding", help="指摘を追加する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--review-id", required=True)
    p.add_argument("--finding-json", required=True, help="Finding の JSON 文字列")

    p = sub.add_parser("resolve-finding", help="指摘の採否を記録する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--review-id", required=True)
    p.add_argument("--finding-id", required=True)
    p.add_argument("--resolution", required=True,
                   choices=["accepted", "rejected", "deferred"])
    p.add_argument("--note", default="")

    p = sub.add_parser("complete-review", help="レビューを完了する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--review-id", required=True)
    p.add_argument("--assessment", required=True)
    p.add_argument("--proceed", default=None, choices=["true", "false"])

    p = sub.add_parser("create-approval", help="承認レコードを作成する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--approval-id", required=True)
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--decision", required=True,
                   choices=["approved", "rejected", "conditional_approval"])
    p.add_argument("--decided-by", default="")
    p.add_argument("--review-ids", default="")
    p.add_argument("--conditions", default="")
    p.add_argument("--rejection-reason", default="")

    p = sub.add_parser("status", help="レビュー・承認状況を表示する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--artifact-id", default="")

    dispatch = {
        "create-review": cmd_create_review,
        "add-finding": cmd_add_finding,
        "resolve-finding": cmd_resolve_finding,
        "complete-review": cmd_complete_review,
        "create-approval": cmd_create_approval,
        "status": cmd_review_status,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
