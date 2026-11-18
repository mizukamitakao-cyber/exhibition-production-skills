#!/usr/bin/env python3
"""
展示構成表管理CLI。
exhibition-story-designer スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.models.story_structure import StorySection
from core.story_designer import (
    StoryError,
    add_section,
    build_structure_md,
    create_story_structure,
    get_story_dir,
    load_story_structure,
    reorder_sections,
    save_story_structure,
    set_story_status,
    update_section,
)
from core.storage import atomic_write


def cmd_create(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    structure = create_story_structure(args.project_id, args.version)
    if args.overall_narrative:
        structure.overall_narrative = args.overall_narrative
    save_story_structure(structure, project_dir)
    print(json.dumps({
        "status": "created",
        "project_id": args.project_id,
        "version": structure.version,
    }))


def cmd_add_section(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    structure = load_story_structure(project_dir, args.version)
    if structure is None:
        print(json.dumps({"status": "error", "message": "story-structure が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    try:
        import json as _json
        section_data = _json.loads(args.section_json)
        section = StorySection(**section_data)
        add_section(structure, section)
    except StoryError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_story_structure(structure, project_dir)
    _save_md(structure, project_dir)
    print(json.dumps({
        "status": "added",
        "section_id": section.section_id,
        "total_sections": len(structure.sections),
    }))


def cmd_reorder(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    structure = load_story_structure(project_dir, args.version)
    if structure is None:
        print(json.dumps({"status": "error", "message": "story-structure が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    ordered_ids = [s.strip() for s in args.ordered_ids.split(",") if s.strip()]
    try:
        reorder_sections(structure, ordered_ids)
    except StoryError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    save_story_structure(structure, project_dir)
    _save_md(structure, project_dir)
    print(json.dumps({"status": "reordered"}))


def cmd_set_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    structure = load_story_structure(project_dir, args.version)
    if structure is None:
        print(json.dumps({"status": "error", "message": "story-structure が見つかりません"}), file=sys.stderr)
        sys.exit(1)

    set_story_status(structure, args.story_status)
    save_story_structure(structure, project_dir)
    print(json.dumps({"status": "updated", "story_status": args.story_status}))


def cmd_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    structure = load_story_structure(project_dir, args.version)
    if structure is None:
        print(json.dumps({"has_structure": False}))
        return
    sections = sorted(structure.sections, key=lambda s: s.display_order)
    print(json.dumps({
        "has_structure": True,
        "project_id": structure.project_id,
        "version": structure.version,
        "status": structure.status,
        "section_count": len(structure.sections),
        "sections": [
            {
                "section_id": s.section_id,
                "title": s.title,
                "display_order": s.display_order,
                "panel_count": s.panel_count,
            }
            for s in sections
        ],
    }))


def _save_md(structure, project_dir: Path) -> None:
    story_dir = get_story_dir(project_dir)
    story_dir.mkdir(exist_ok=True)
    md_path = story_dir / f"story-structure-v{structure.version}.md"
    atomic_write(md_path, build_structure_md(structure))


def main() -> None:
    parser = argparse.ArgumentParser(prog="story_cli", description="展示構成表管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="構成表を新規作成する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--project-id", required=True)
    p.add_argument("--version", type=int, default=1)
    p.add_argument("--overall-narrative", default="")

    p = sub.add_parser("add-section", help="セクションを追加する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--section-json", required=True, help="StorySection の JSON 文字列")
    p.add_argument("--version", type=int, default=None)

    p = sub.add_parser("reorder", help="セクション順序を変更する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--ordered-ids", required=True, help="カンマ区切りのセクションID")
    p.add_argument("--version", type=int, default=None)

    p = sub.add_parser("set-status", help="構成表のステータスを更新する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--story-status", required=True,
                   choices=["draft", "ready_for_review", "approved"])
    p.add_argument("--version", type=int, default=None)

    p = sub.add_parser("status", help="構成表の状態を表示する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--version", type=int, default=None)

    dispatch = {
        "create": cmd_create,
        "add-section": cmd_add_section,
        "reorder": cmd_reorder,
        "set-status": cmd_set_status,
        "status": cmd_status,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
