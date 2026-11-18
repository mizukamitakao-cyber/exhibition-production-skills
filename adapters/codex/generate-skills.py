#!/usr/bin/env python3
"""
Codex Skills 実行層の生成スクリプト（Phase 2 調査後に設計・実装）。

現在の状態:
  OI-11（Codex 固有の Skills/Tools 実行機構の有無）の調査結果待ち。
  調査結果は adapters/codex/README.md に記録する。

設計方針（調査結果による分岐）:
  - Codex 固有の Skills 実行機構が存在する場合:
    その形式（SKILL.md 相当）に変換するスクリプトをここに実装する。
  - 存在しない場合:
    generate-instructions.py に統合するか、このスクリプトを廃止する。
"""

raise NotImplementedError(
    "Codex Skills 実行層の仕様が未確定です。\n"
    "adapters/codex/README.md の OI-11 調査結果を確認してください。"
)
