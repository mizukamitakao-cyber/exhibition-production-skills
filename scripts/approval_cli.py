#!/usr/bin/env python3
"""
承認CLI。
exhibition-museum-onboarding スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.approval import ApprovalError, approve_museum_profile, begin_revision, get_latest_approved_version


def cmd_approve(args: argparse.Namespace) -> None:
    museum_dir = Path(args.museum_dir)
    draft_path = Path(args.draft_path)
    try:
        versioned_path = approve_museum_profile(museum_dir, draft_path, args.approved_by)
        print(json.dumps({
            "status": "approved",
            "versioned_path": str(versioned_path),
        }))
    except ApprovalError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


def cmd_begin_revision(args: argparse.Namespace) -> None:
    museum_dir = Path(args.museum_dir)
    try:
        draft_path = begin_revision(museum_dir, args.version, args.reason)
        print(json.dumps({
            "status": "revision_started",
            "draft_path": str(draft_path),
        }))
    except ApprovalError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


def cmd_latest_version(args: argparse.Namespace) -> None:
    museum_dir = Path(args.museum_dir)
    version = get_latest_approved_version(museum_dir)
    print(json.dumps({"latest_version": version}))


def main() -> None:
    parser = argparse.ArgumentParser(prog="approval_cli", description="承認・保護管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("approve", help="プロファイルドラフトを承認する")
    p.add_argument("--museum-dir", required=True)
    p.add_argument("--draft-path", required=True)
    p.add_argument("--approved-by", default=None)

    p = sub.add_parser("begin-revision", help="承認済みプロファイルの改訂を開始する")
    p.add_argument("--museum-dir", required=True)
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--reason", default="")

    p = sub.add_parser("latest-version", help="最新の承認済みバージョン番号を取得する")
    p.add_argument("--museum-dir", required=True)

    dispatch = {
        "approve": cmd_approve,
        "begin-revision": cmd_begin_revision,
        "latest-version": cmd_latest_version,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
