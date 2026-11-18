#!/usr/bin/env python3
"""core/skills/ のスキルを Claude Code のスキルディレクトリにインストールする。"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CORE_SKILLS = PROJECT_ROOT / "core" / "skills"


def deploy_skills(skills_root: Path) -> None:
    if not CORE_SKILLS.exists():
        print(f"スキルディレクトリが存在しません: {CORE_SKILLS}")
        return

    skills_root.mkdir(parents=True, exist_ok=True)
    installed = 0

    for skill_dir in sorted(CORE_SKILLS.iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = skills_root / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        print(f"  インストール: {skill_dir.name} → {dest}")
        installed += 1

    if installed == 0:
        print("インストール対象のスキルがありません。")
    else:
        print(f"\n{installed} 件のスキルをインストールしました。")


def main() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))

    try:
        from core.config import load_deployment_config
        config = load_deployment_config()
        skills_root = Path(config.skills_root).expanduser()
    except FileNotFoundError:
        print("deployment.yaml が見つかりません。デフォルトパスを使用します。")
        skills_root = Path.home() / ".claude" / "skills"

    print(f"スキルインストール先: {skills_root}")
    deploy_skills(skills_root)


if __name__ == "__main__":
    main()
