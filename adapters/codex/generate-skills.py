#!/usr/bin/env python3
"""
Codex 向けスキルデプロイスクリプト。
core/skills/ から .agents/skills/ へスキルをコピーする。

Codex は Agent Skills open standard (agentskills.io) をサポートし、
SKILL.md フォーマットは Claude Code と共通。
スキルディレクトリのみ異なる:
  Claude Code: ~/.claude/skills/<name>/ または .claude/skills/<name>/
  Codex      : $HOME/.agents/skills/<name>/ または .agents/skills/<name>/
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_SKILLS = PROJECT_ROOT / "core" / "skills"


def deploy_to_codex(scope: str = "project") -> None:
    """
    scope: "project" → .agents/skills/ (リポジトリ内、チーム共有)
           "user"    → $HOME/.agents/skills/ (ユーザーローカル)
    """
    if scope == "user":
        dest_root = Path.home() / ".agents" / "skills"
    else:
        dest_root = PROJECT_ROOT / ".agents" / "skills"

    if not CORE_SKILLS.exists():
        print(f"スキルディレクトリが存在しません: {CORE_SKILLS}")
        return

    dest_root.mkdir(parents=True, exist_ok=True)
    installed = 0

    for skill_dir in sorted(CORE_SKILLS.iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = dest_root / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        print(f"  インストール: {skill_dir.name} → {dest}")
        installed += 1

    if installed == 0:
        print("インストール対象のスキルがありません。")
    else:
        print(f"\n{installed} 件のスキルを Codex ({scope}) にインストールしました。")


if __name__ == "__main__":
    scope_arg = sys.argv[1] if len(sys.argv) > 1 else "project"
    sys.path.insert(0, str(PROJECT_ROOT))
    deploy_to_codex(scope=scope_arg)
