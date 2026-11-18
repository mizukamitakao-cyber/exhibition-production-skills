#!/usr/bin/env python3
"""
出典管理CLI。
exhibition-researcher スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.models.source_registry import Source
from core.researcher import (
    ResearchError,
    add_source,
    create_source_registry,
    get_unverified_sources,
    load_registry,
    load_research_memo,
    mark_unverified,
    mark_verified,
    record_usage,
    save_registry,
    save_research_memo,
    update_source,
)


def cmd_create(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    registry = create_source_registry(args.project_id)
    save_registry(registry, project_dir)
    print(json.dumps({"status": "created", "project_id": args.project_id}))


def cmd_add_source(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    registry = load_registry(project_dir)
    if registry is None:
        print(json.dumps({"status": "error", "message": "source-registry.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        import json as _json
        source_data = _json.loads(args.source_json)
        source = Source(**source_data)
        add_source(registry, source)
    except ResearchError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_registry(registry, project_dir)
    print(json.dumps({
        "status": "added",
        "source_id": source.source_id,
        "total_sources": len(registry.sources),
    }))


def cmd_mark_verified(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    registry = load_registry(project_dir)
    if registry is None:
        print(json.dumps({"status": "error", "message": "source-registry.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        mark_verified(registry, args.source_id)
    except ResearchError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_registry(registry, project_dir)
    print(json.dumps({"status": "verified", "source_id": args.source_id}))


def cmd_record_usage(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    registry = load_registry(project_dir)
    if registry is None:
        print(json.dumps({"status": "error", "message": "source-registry.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        record_usage(registry, args.source_id, args.artifact_id, args.sections or "")
    except ResearchError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_registry(registry, project_dir)
    print(json.dumps({"status": "usage_recorded"}))


def cmd_save_memo(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    path = save_research_memo(project_dir, args.memo_id, args.content)
    print(json.dumps({"status": "saved", "path": str(path)}))


def cmd_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    registry = load_registry(project_dir)
    if registry is None:
        print(json.dumps({"has_registry": False}))
        return
    unverified = get_unverified_sources(registry)
    print(json.dumps({
        "has_registry": True,
        "project_id": registry.project_id,
        "total_sources": len(registry.sources),
        "unverified_count": len(unverified),
        "sources": [
            {
                "source_id": s.source_id,
                "title": s.title,
                "type": s.type,
                "verification_status": s.verification_status,
            }
            for s in registry.sources
        ],
    }))


def cmd_get_unverified(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    registry = load_registry(project_dir)
    if registry is None:
        print(json.dumps({"has_registry": False, "unverified": []}))
        return
    unverified = get_unverified_sources(registry)
    print(json.dumps({
        "has_registry": True,
        "unverified": [
            {"source_id": s.source_id, "title": s.title, "type": s.type}
            for s in unverified
        ],
    }))


def main() -> None:
    parser = argparse.ArgumentParser(prog="research_cli", description="出典管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="出典台帳を作成する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--project-id", required=True)

    p = sub.add_parser("add-source", help="出典を追加する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--source-json", required=True, help="Source の JSON 文字列")

    p = sub.add_parser("mark-verified", help="出典を確認済みにする")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--source-id", required=True)

    p = sub.add_parser("record-usage", help="出典の使用箇所を記録する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--sections", default="")

    p = sub.add_parser("save-memo", help="調査メモを保存する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--memo-id", required=True)
    p.add_argument("--content", required=True)

    p = sub.add_parser("status", help="出典台帳の状態を表示する")
    p.add_argument("--project-dir", required=True)

    p = sub.add_parser("get-unverified", help="未確認出典一覧を取得する")
    p.add_argument("--project-dir", required=True)

    dispatch = {
        "create": cmd_create,
        "add-source": cmd_add_source,
        "mark-verified": cmd_mark_verified,
        "record-usage": cmd_record_usage,
        "save-memo": cmd_save_memo,
        "status": cmd_status,
        "get-unverified": cmd_get_unverified,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
