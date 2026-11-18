#!/usr/bin/env python3
"""
Visual Designer CLI。
exhibition-visual-designer スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.visual_designer import (
    generate_panel_html,
    list_layouts,
    load_panel_layout,
    save_design_concept,
    save_panel_layout,
)


def _load_panel_specs(project_dir: Path) -> dict:
    """館プロファイルから panel_specs を読み込む。なければ空 dict を返す。"""
    try:
        import sys as _sys
        from core.director import get_project_dir, load_project
        from core.approval import find_latest_approved_profile

        project = load_project(project_dir)
        profile_path = find_latest_approved_profile(project_dir.parent)
        if profile_path is None:
            return {}
        from ruamel.yaml import YAML
        yaml = YAML()
        data = yaml.load(profile_path)
        return data.get("design", {}).get("panel_specs", {}) if data else {}
    except Exception:
        return {}


def cmd_generate(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)

    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
    else:
        content = args.content or ""

    panel_specs = _load_panel_specs(project_dir)

    # CLI オプションで panel_specs を上書き
    if args.bg_color:
        panel_specs["bg_color"] = args.bg_color
    if args.accent_color:
        panel_specs["accent_color"] = args.accent_color
    if args.panel_width:
        panel_specs["panel_width"] = args.panel_width

    html = generate_panel_html(
        panel_id=args.panel_id,
        title=args.title,
        markdown_content=content,
        panel_specs=panel_specs,
        footer=args.footer or "",
    )
    path = save_panel_layout(project_dir, args.panel_id, html)
    print(json.dumps({
        "status": "generated",
        "panel_id": args.panel_id,
        "path": str(path),
    }))


def cmd_save_concept(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
    else:
        content = args.content or ""
    path = save_design_concept(project_dir, content)
    print(json.dumps({"status": "saved", "path": str(path)}))


def cmd_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir)
    layouts = list_layouts(project_dir)
    concept_path = project_dir / "design" / "concept.md"
    print(json.dumps({
        "layout_count": len(layouts),
        "layouts": layouts,
        "concept_exists": concept_path.exists(),
    }))


def main() -> None:
    parser = argparse.ArgumentParser(prog="visual_designer_cli", description="Visual Designer")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("generate", help="パネルHTMLを生成する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--panel-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--content", default="")
    p.add_argument("--content-file", default="")
    p.add_argument("--footer", default="")
    p.add_argument("--bg-color", default="")
    p.add_argument("--accent-color", default="")
    p.add_argument("--panel-width", default="")

    p = sub.add_parser("save-concept", help="デザインコンセプト文書を保存する")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--content", default="")
    p.add_argument("--content-file", default="")

    p = sub.add_parser("status", help="生成済みレイアウト一覧を表示する")
    p.add_argument("--project-dir", required=True)

    dispatch = {
        "generate": cmd_generate,
        "save-concept": cmd_save_concept,
        "status": cmd_status,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
