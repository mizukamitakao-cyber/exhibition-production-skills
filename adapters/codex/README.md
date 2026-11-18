# Codex VS Code アダプター

## アーキテクチャ（確定版）

Codex アダプターは 2 層構造で設計する。

| 層 | ファイル | 役割 | 対応するClaude Code側 |
|---|---------|------|--------------------|
| 指示層 | `generate-instructions.py` → `AGENTS.md` | Codex に定常的なプロジェクト指示を提供 | `CLAUDE.md` |
| 実行層 | `generate-skills.py` → `.agents/skills/` | スキルを Codex に配置 | `.claude/skills/` |

SKILL.md フォーマットは **Agent Skills open standard**（agentskills.io）で共通化されており、
`core/skills/` のスキルは Claude Code・Codex の両方にそのままデプロイできる。

---

## OI-11 調査結果（Codex 固有 Skills/Tools 実行機構）

**調査ステータス:** 確定（2026-11-18 Phase 2 タスク 2-11）

**結論:** Codex は Agent Skills open standard をサポートし、SKILL.md を認識する。

**詳細:**
- Codex CLI および VS Code 拡張は `.agents/skills/<name>/SKILL.md` を読み込む
- SKILL.md フォーマットは Anthropic が開発・公開した Agent Skills open standard（2025年12月公開）に準拠
- Claude Code の SKILL.md とフォーマットが共通（`core/skills/` を両方に流用可能）
- 配置先ディレクトリのみ異なる:
  - Claude Code: `~/.claude/skills/<name>/` または `.claude/skills/<name>/`
  - Codex: `$HOME/.agents/skills/<name>/` または `.agents/skills/<name>/`

**スキルの検索順序（Codex）:**
1. 作業ディレクトリから git ルートに向けて `.agents/skills/<name>/`
2. `$HOME/.agents/skills/<name>/`
3. `/etc/codex/skills/<name>/`

---

## OI-02 調査結果（AGENTS.md の制約）

**調査ステータス:** 確定（2026-11-18 Phase 2 タスク 2-11）

**結論:** AGENTS.md の制約は実用上問題なし。

**詳細:**
- Codex の AGENTS.md デフォルトサイズ上限: **32 KiB**（約32,000文字）
- 本プロジェクトの AGENTS.md 推定サイズ: ~7 KB（11スキル × ~500文字 + ベーステンプレート）
- 上限に対して余裕あり

**AGENTS.md の役割（確定）:**
- プロジェクト全体の定常指示（コーディング規約・セキュリティルール等）
- スキル一覧と起動条件の概要
- スキルの詳細指示は `.agents/skills/<name>/SKILL.md` に分離する

---

## デプロイ手順

### Claude Code 向け
```bash
python scripts/deploy.py
```

### Codex 向け（プロジェクトスコープ）
```bash
python adapters/codex/generate-skills.py project
python adapters/codex/generate-instructions.py
```

### Codex 向け（ユーザースコープ）
```bash
python adapters/codex/generate-skills.py user
```

---

## 設計決定（確定）

| 項目 | 確定内容 |
|------|---------|
| Skills 実行機構 | Agent Skills open standard 対応。SKILL.md フォーマット共通 |
| AGENTS.md 上限 | 32 KiB（余裕あり） |
| スキル配置先 | `.agents/skills/`（project）または `$HOME/.agents/skills/`（user） |
| Phase 7 での実装範囲 | スキルは Phase 3〜6 で core/skills/ に作成し、Phase 7 で Codex 動作検証する |
