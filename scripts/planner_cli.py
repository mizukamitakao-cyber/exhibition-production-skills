#!/usr/bin/env python3
"""
企画書管理CLI。
exhibition-planner スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.models.artifact_manifest import Artifact
from core.planner import (
    PlannerError,
    add_artifact,
    create_artifact_manifest,
    get_artifact,
    get_latest_plan_version,
    load_artifact_manifest,
    load_plan_draft,
    register_plan_artifact,
    save_artifact_manifest,
    save_plan_draft,
    update_artifact_status,
)


def cmd_create(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    manifest = create_artifact_manifest(args.project_id)
    save_artifact_manifest(manifest, project_dir)
    print(json.dumps({"status": "created", "project_id": args.project_id}))


def cmd_save_plan(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    version = args.version
    if version is None:
        latest = get_latest_plan_version(project_dir)
        version = latest + 1

    plan_path = save_plan_draft(project_dir, args.content, version)

    manifest = load_artifact_manifest(project_dir)
    if manifest is None:
        from core.director import load_project
        project_path = project_dir / "exhibition-project.yaml"
        project = load_project(project_path)
        manifest = create_artifact_manifest(project.project_id)

    artifact_id = f"plan-v{version}"
    existing = get_artifact(manifest, artifact_id)
    if existing is None:
        register_plan_artifact(manifest, project_dir, version, args.title or "")
    else:
        from datetime import datetime, timezone
        existing.updated_at = datetime.now(timezone.utc).isoformat()

    save_artifact_manifest(manifest, project_dir)
    print(json.dumps({
        "status": "saved",
        "version": version,
        "path": str(plan_path),
        "artifact_id": artifact_id,
    }))


def cmd_set_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    manifest = load_artifact_manifest(project_dir)
    if manifest is None:
        print(json.dumps({"status": "error", "message": "artifact-manifest.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        update_artifact_status(manifest, args.artifact_id, args.artifact_status)
    except PlannerError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_artifact_manifest(manifest, project_dir)
    print(json.dumps({"status": "updated", "artifact_id": args.artifact_id, "new_status": args.artifact_status}))


def cmd_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    manifest = load_artifact_manifest(project_dir)
    if manifest is None:
        print(json.dumps({"has_manifest": False}))
        return
    latest_version = get_latest_plan_version(project_dir)
    print(json.dumps({
        "has_manifest": True,
        "project_id": manifest.project_id,
        "latest_plan_version": latest_version,
        "artifacts": [
            {
                "artifact_id": a.artifact_id,
                "type": a.type,
                "title": a.title,
                "version": a.version,
                "status": a.status,
            }
            for a in manifest.artifacts
        ],
    }))


def main() -> None:
    parser = argparse.ArgumentParser(prog="planner_cli", description="企画書管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="成果物マニフェストを作成する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--project-id", required=True)

    p = sub.add_parser("save-plan", help="企画書を保存する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--version", type=int, default=None)
    p.add_argument("--title", default="")

    p = sub.add_parser("set-status", help="成果物のステータスを更新する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--artifact-status", required=True,
                   choices=["draft", "ready_for_review", "approved", "superseded"])

    p = sub.add_parser("status", help="成果物マニフェストの状態を表示する")
    p.add_argument("--project-dir", required=True)

    dispatch = {
        "create": cmd_create,
        "save-plan": cmd_save_plan,
        "set-status": cmd_set_status,
        "status": cmd_status,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
