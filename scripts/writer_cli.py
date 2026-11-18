#!/usr/bin/env python3
"""
原稿管理CLI。
exhibition-writer スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.planner import (
    load_artifact_manifest,
    save_artifact_manifest,
    update_artifact_status,
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


def cmd_save(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    version = args.version
    if version is None:
        version = get_latest_manuscript_version(project_dir, args.panel_id) + 1
        if version == 1:
            version = 1  # 新規

    path = save_manuscript(project_dir, args.panel_id, args.content, version)

    manifest = load_artifact_manifest(project_dir)
    if manifest is not None:
        register_manuscript_artifact(
            manifest, project_dir, args.panel_id, version,
            title=args.title or "",
        )
        save_artifact_manifest(manifest, project_dir)

    print(json.dumps({
        "status": "saved",
        "panel_id": args.panel_id,
        "version": version,
        "path": str(path),
    }))


def cmd_start_revision(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    try:
        new_version, original_content = create_revision_manuscript(
            project_dir, args.panel_id, args.current_version
        )
    except WriterError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "status": "revision_started",
        "panel_id": args.panel_id,
        "new_version": new_version,
        "original_content_length": len(original_content),
    }))


def cmd_set_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    manifest = load_artifact_manifest(project_dir)
    if manifest is None:
        print(json.dumps({"status": "error", "message": "artifact-manifest.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    from core.planner import PlannerError
    try:
        update_artifact_status(manifest, args.artifact_id, args.artifact_status)
    except PlannerError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_artifact_manifest(manifest, project_dir)
    print(json.dumps({"status": "updated", "artifact_id": args.artifact_id, "new_status": args.artifact_status}))


def cmd_check_prerequisite(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    manifest = load_artifact_manifest(project_dir)
    if manifest is None:
        print(json.dumps({"approved": False, "reason": "manifest が見つかりません"}))
        return
    approved = check_prerequisite_approved(manifest, args.artifact_id)
    print(json.dumps({"approved": approved, "artifact_id": args.artifact_id}))


def cmd_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    manuscripts = list_manuscripts(project_dir)
    manifest = load_artifact_manifest(project_dir)
    artifact_statuses: dict[str, str] = {}
    if manifest is not None:
        artifact_statuses = {
            a.artifact_id: a.status
            for a in manifest.artifacts
            if a.type == "manuscript"
        }
    for ms in manuscripts:
        artifact_id = f"{ms['panel_id']}-v{ms['version']}"
        ms["artifact_status"] = artifact_statuses.get(artifact_id, "not_registered")
    print(json.dumps({
        "manuscript_count": len(manuscripts),
        "manuscripts": manuscripts,
    }))


def main() -> None:
    parser = argparse.ArgumentParser(prog="writer_cli", description="原稿管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("save", help="原稿を保存する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--panel-id", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--version", type=int, default=None)
    p.add_argument("--title", default="")

    p = sub.add_parser("start-revision", help="改訂版の準備をする（原本は保持）")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--panel-id", required=True)
    p.add_argument("--current-version", type=int, default=None)

    p = sub.add_parser("set-status", help="原稿のステータスを更新する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--artifact-status", required=True,
                   choices=["draft", "ready_for_review", "approved", "superseded"])

    p = sub.add_parser("check-prerequisite", help="前提成果物が approved か確認する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--artifact-id", required=True)

    p = sub.add_parser("status", help="原稿一覧を表示する")
    p.add_argument("--project-dir", required=True)

    dispatch = {
        "save": cmd_save,
        "start-revision": cmd_start_revision,
        "set-status": cmd_set_status,
        "check-prerequisite": cmd_check_prerequisite,
        "status": cmd_status,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
