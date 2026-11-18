#!/usr/bin/env python3
"""AGENTS.md を生成する（Codex VS Code 用指示ファイル・指示層）。"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_SKILLS = PROJECT_ROOT / "core" / "skills"
BASE_TEMPLATE = Path(__file__).parent / "AGENTS.md.base"
OUTPUT = PROJECT_ROOT / "AGENTS.md"


def generate_agents_md() -> None:
    base = BASE_TEMPLATE.read_text(encoding="utf-8") if BASE_TEMPLATE.exists() else ""

    skills_section_parts: list[str] = []
    if CORE_SKILLS.exists():
        for skill_dir in sorted(CORE_SKILLS.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding="utf-8")
                skills_section_parts.append(f"\n### {skill_dir.name}\n\n{content}")

    agents_content = base.replace("{{SKILLS_SECTION}}", "\n".join(skills_section_parts))
    OUTPUT.write_text(agents_content, encoding="utf-8")
    print(f"生成完了: {OUTPUT}")


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_ROOT))
    generate_agents_md()
