#!/usr/bin/env python3
"""
アイディア管理CLI。
exhibition-idea-generator スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.ideas import (
    IdeaError,
    add_idea,
    create_idea_list,
    load_idea_list,
    reject_idea,
    save_comparison_md,
    save_idea_list,
    select_idea,
)
from core.models.idea_list import IdeaEntry


def cmd_create(args: argparse.Namespace) -> None:
    from core.director import load_project
    project_path = Path(args.project_path)
    project = load_project(project_path)

    idea_list = create_idea_list(project.project_id, project.museum_id, args.brief_summary)
    project_dir = project_path.parent
    save_idea_list(idea_list, project_dir)
    print(json.dumps({"status": "created", "project_id": project.project_id}))


def cmd_add(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    idea_list = load_idea_list(project_dir)
    if idea_list is None:
        print(json.dumps({"status": "error", "message": "idea-list.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        import json as _json
        idea_data = _json.loads(args.idea_json)
        entry = IdeaEntry(**idea_data)
        add_idea(idea_list, entry)
    except IdeaError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_idea_list(idea_list, project_dir)
    save_comparison_md(idea_list, project_dir)
    print(json.dumps({"status": "added", "idea_id": entry.id, "total_ideas": len(idea_list.ideas)}))


def cmd_select(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    idea_list = load_idea_list(project_dir)
    if idea_list is None:
        print(json.dumps({"status": "error", "message": "idea-list.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        select_idea(idea_list, args.idea_id)
    except IdeaError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_idea_list(idea_list, project_dir)
    save_comparison_md(idea_list, project_dir)
    print(json.dumps({"status": "selected", "idea_id": args.idea_id}))


def cmd_reject(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    idea_list = load_idea_list(project_dir)
    if idea_list is None:
        print(json.dumps({"status": "error", "message": "idea-list.yaml が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        reject_idea(idea_list, args.idea_id, args.reason)
    except IdeaError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_idea_list(idea_list, project_dir)
    save_comparison_md(idea_list, project_dir)
    print(json.dumps({"status": "rejected", "idea_id": args.idea_id}))


def cmd_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    idea_list = load_idea_list(project_dir)
    if idea_list is None:
        print(json.dumps({"has_ideas": False}))
        return
    print(json.dumps({
        "has_ideas": True,
        "project_id": idea_list.project_id,
        "idea_count": len(idea_list.ideas),
        "selected_idea_id": idea_list.selected_idea_id,
        "ideas": [
            {"id": i.id, "title": i.title, "status": i.status}
            for i in idea_list.ideas
        ],
    }))


def main() -> None:
    parser = argparse.ArgumentParser(prog="idea_cli", description="アイディア管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="アイディアリストを作成する")
    p.add_argument("--project-path", required=True)
    p.add_argument("--brief-summary", default="")

    p = sub.add_parser("add", help="アイディアを追加する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--idea-json", required=True, help="IdeaEntry の JSON 文字列")

    p = sub.add_parser("select", help="アイディアを選定する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--idea-id", required=True)

    p = sub.add_parser("reject", help="アイディアを却下する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--idea-id", required=True)
    p.add_argument("--reason", default="")

    p = sub.add_parser("status", help="アイディア一覧を表示する")
    p.add_argument("--project-dir", required=True)

    dispatch = {
        "create": cmd_create,
        "add": cmd_add,
        "select": cmd_select,
        "reject": cmd_reject,
        "status": cmd_status,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
