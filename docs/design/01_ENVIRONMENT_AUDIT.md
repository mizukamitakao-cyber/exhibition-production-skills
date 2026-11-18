# 01 開発環境調査記録

調査日：2026年11月18日  
文書区分：Phase 1 環境調査  
ステータス：確定

---

## 1. 作業環境

| 項目 | 値 |
|------|----|
| 作業ディレクトリ | `C:\Users\mizukami\Documents\exhibition-production-skills` |
| Gitリポジトリ | 未初期化（Git管理なし） |
| 既存ファイル | `docs/` のみ（指示書・基本構想の2文書） |
| 他プロジェクトへの影響 | なし（独立した空のプロジェクトフォルダ） |
| OS | Windows 11 Pro 10.0.26300 |
| シェル | PowerShell（Bashも利用可） |

## 2. 開発ツール

| ツール | バージョン | 備考 |
|--------|-----------|------|
| Python | 3.13.12（主）/ 3.14.6（別系統） | pip 25.3 |
| Git | 2.54.0.windows.1 | 利用可能 |
| Node.js | 24.16.0 | npm 11.13.0 |
| Claude Code | 2.1.172 | 現在の実行環境 |

## 3. Claude Code スキル構造

既存スキル（`legal-advisor`、`research-assistant`）から確認した構造：

```
~/.claude/skills/<skill-name>/
├── SKILL.md          # フロントマター（name/description）＋指示本文
├── README.md         # ドキュメント（Skill外からの参照用）
├── references/       # コンテキスト注入用参照文書
│   └── function-*.md
└── templates/
    ├── config.template.yaml  # ユーザー設定テンプレート
    └── *.template.md         # 成果物テンプレート
```

**SKILL.mdのフロントマター形式：**
```yaml
---
name: <skill-name>
description: <スキルの説明文（トリガー条件を含む）>
---
```

**スキルの配置場所：**  
既存スキルはすべてグローバル（`~/.claude/skills/`）に配置されている。  
プロジェクトレベル（`.claude/skills/`）での配置は仕様上存在する可能性があるが、現環境では未確認。Phase 2開始前に要検証。

**スキルの呼び出し：**  
`/skill-name` コマンドでユーザーが明示的に呼び出す、またはCLAUDE.mdのトリガー条件による自動起動。

## 4. OpenAI Codex (VS Code) 仕様

| 項目 | 状態 | 内容 |
|------|------|------|
| 製品特定 | 確定 | OpenAI Codex（VS Code環境） |
| 指示ファイル（指示層） | 既知 | `AGENTS.md`（リポジトリルート、または `~/.codex/AGENTS.md`）。Claude Codeの `CLAUDE.md` に相当 |
| スキル実行機構（実行層） | 未確認 | Claude Codeの `SKILL.md` / `/skill-name` に相当する固有機構の有無は未検証。Phase 2初期に調査（OI-11） |
| AGENTS.md制約 | 未確認 | 文字数上限・セクション形式等の制約はPhase 2初期に確認（OI-02） |
| 命令の読み込み | 既知 | `AGENTS.md` を実行コンテキストに自動注入 |

**Codexアダプターの2層構造（現設計）：**  
- **指示層**：`adapters/codex/generate-instructions.py` が `AGENTS.md` を生成（CLAUDE.md相当）  
- **実行層**：`adapters/codex/generate-skills.py` の設計はOI-11調査結果を受けてPhase 2中に確定  

詳細は `02_ARCHITECTURE_DESIGN.md` 参照。

## 5. Windows 制約

| 制約 | 内容 | 対応方針 |
|------|------|---------|
| パス区切り | `\`（PowerShell/Windows）vs `/`（YAML/JSON標準） | Python `pathlib.Path` で統一処理、YAML内はスラッシュ表記 |
| シンボリックリンク | 管理者権限またはDeveloper Modeが必要 | 設計でシンボリックリンクを使用しない |
| ファイル権限 | Windows ACL（UNIXパーミッションとは異なる） | 書き込み禁止は属性（読み取り専用）で管理 |
| パス長制限 | デフォルト260文字（MAX_PATH） | ネストを浅くする設計、必要時はLongPathsEnabled対応 |
| 大文字・小文字 | ファイルシステムはデフォルト非区別 | IDとパスはすべて小文字・ケバブケースで統一 |

## 6. 既存プロジェクトへの影響

他プロジェクト（`~/.claude/projects/` 配下に複数確認）への影響：

- 本プロジェクトのスキルはグローバルインストール時に `~/.claude/skills/` を変更するが、スキル名が重複しない限り既存スキルに影響なし。
- スキル名の命名規則として `exhibition-` プレフィックスを採用し、既存スキルとの衝突を回避する。

## 7. 未確認事項

| 項目 | 影響 | 確認時期 |
|------|------|---------|
| Claude Codeのプロジェクトレベルスキル配置動作 | スキル配布・インストール方式に影響 | Phase 2実装前 |
| OpenAI Codex VS Code の具体的バージョン・機能差（OI-02・OI-11） | Codexアダプター実行層の設計に影響 | Phase 2初期 |
| `exhibition-production-data/` の実際の作成タイミング | Deployment Setupの手順に影響 | Phase 2設計時 |
