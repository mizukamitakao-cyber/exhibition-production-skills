#!/usr/bin/env python3
"""
展示プロジェクト管理CLI。
exhibition-director スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.director import (
    advance_project_phase,
    create_project,
    get_latest_approved_profile_path,
    get_project_dir,
    list_projects,
    load_project,
    save_project,
)


def cmd_create(args: argparse.Namespace) -> None:
    museum_dir = Path(args.museum_dir)
    project_dir = get_project_dir(museum_dir, args.project_id)

    profile_path = get_latest_approved_profile_path(museum_dir)
    if not profile_path:
        print(json.dumps({"status": "error", "message": "承認済みプロファイルが見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        profile_version = int(profile_path.stem.split("-v")[1])
    except (IndexError, ValueError):
        profile_version = 1

    project_dir.mkdir(parents=True, exist_ok=True)
    project_path = project_dir / "exhibition-project.yaml"
    if project_path.exists():
        print(json.dumps({"status": "error", "message": "プロジェクトが既に存在します"}), file=sys.stderr)
        sys.exit(1)

    project = create_project(
        project_id=args.project_id,
        museum_id=args.museum_id,
        title=args.title,
        profile_version=profile_version,
    )
    save_project(project, project_path)
    print(json.dumps({
        "status": "created",
        "project_id": project.project_id,
        "project_path": str(project_path),
        "profile_version": profile_version,
    }))


def cmd_status(args: argparse.Namespace) -> None:
    project = load_project(Path(args.project_path))
    print(json.dumps({
        "project_id": project.project_id,
        "museum_id": project.museum_id,
        "title": project.title,
        "status": project.status,
        "current_phase": project.current_phase,
        "completed_phases": project.completed_phases,
        "brief": {
            "theme": project.brief.theme,
            "target_visitors": project.brief.target_visitors,
            "period": project.brief.period,
        },
    }))


def cmd_list(args: argparse.Namespace) -> None:
    museum_dir = Path(args.museum_dir)
    projects = []
    for path in list_projects(museum_dir):
        project = load_project(path)
        projects.append({
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "current_phase": project.current_phase,
            "project_path": str(path),
        })
    print(json.dumps({"projects": projects}))


def cmd_check_prerequisites(args: argparse.Namespace) -> None:
    museum_dir = Path(args.museum_dir)
    profile_path = get_latest_approved_profile_path(museum_dir)
    print(json.dumps({
        "has_approved_profile": profile_path is not None,
        "profile_path": str(profile_path) if profile_path else None,
    }))


def cmd_advance_phase(args: argparse.Namespace) -> None:
    project = load_project(Path(args.project_path))
    advance_project_phase(project, args.phase_name)
    save_project(project, Path(args.project_path))
    print(json.dumps({
        "status": "advanced",
        "current_phase": project.current_phase,
        "completed_phases": project.completed_phases,
    }))


def cmd_update_brief(args: argparse.Namespace) -> None:
    """プロジェクトのブリーフ（概要）を更新する。"""
    project = load_project(Path(args.project_path))
    if args.theme is not None:
        project.brief.theme = args.theme
    if args.period is not None:
        project.brief.period = args.period
    if args.venue is not None:
        project.brief.venue = args.venue
    if args.target_visitors is not None:
        project.brief.target_visitors = [
            v.strip()
            for v in args.target_visitors.replace("、", ",").split(",")
            if v.strip()
        ]
    if args.constraints is not None:
        project.brief.constraints = [
            c.strip()
            for c in args.constraints.replace("、", ",").split(",")
            if c.strip()
        ]
    save_project(project, Path(args.project_path))
    print(json.dumps({"status": "brief_updated"}))


def main() -> None:
    parser = argparse.ArgumentParser(prog="project_cli", description="展示プロジェクト管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="新規プロジェクトを作成する")
    p.add_argument("--project-id", required=True)
    p.add_argument("--museum-id", required=True)
    p.add_argument("--museum-dir", required=True)
    p.add_argument("--title", default="")

    p = sub.add_parser("status", help="プロジェクト状態を表示する")
    p.add_argument("--project-path", required=True)

    p = sub.add_parser("list", help="プロジェクト一覧を表示する")
    p.add_argument("--museum-dir", required=True)

    p = sub.add_parser("check-prerequisites", help="前提条件（承認済みプロファイル）を確認する")
    p.add_argument("--museum-dir", required=True)

    p = sub.add_parser("advance-phase", help="フェーズを進める")
    p.add_argument("--project-path", required=True)
    p.add_argument("--phase-name", required=True)

    p = sub.add_parser("update-brief", help="プロジェクトのブリーフを更新する")
    p.add_argument("--project-path", required=True)
    p.add_argument("--theme", default=None)
    p.add_argument("--period", default=None)
    p.add_argument("--venue", default=None)
    p.add_argument("--target-visitors", default=None)
    p.add_argument("--constraints", default=None)

    dispatch = {
        "create": cmd_create,
        "status": cmd_status,
        "list": cmd_list,
        "check-prerequisites": cmd_check_prerequisites,
        "advance-phase": cmd_advance_phase,
        "update-brief": cmd_update_brief,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
