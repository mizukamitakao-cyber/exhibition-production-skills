# Development Log — 企画展示制作AI Skills

---

## 2026-11-18 ── Phase 1 完了

### 実施内容

**環境調査**
- Python 3.13.12 / Git 2.54.0.windows.1 / Node.js 24.16.0 / Claude Code 2.1.172 を確認
- 既存スキル（`legal-advisor`、`research-assistant`）からSKILL.mdフォーマットを確認
- プロジェクトレベルスキル配置（`.claude/skills/`）は未確認 → OI-01として記録

**設計文書作成（`docs/design/` 9文書）**

| 文書 | 主要な設計決定 |
|------|--------------|
| 01 環境調査 | 調査結果の正式記録 |
| 02 アーキテクチャ設計 | Codexアダプター2層構造（指示層/実行層）、4階層設定（common→domain→museum→project）、`deployment.yaml.template` ＋ `.gitignore` 分離 |
| 03 データモデル設計 | 9モデル定義、pydantic v2採用、JSON Schema自動生成方式、`source_usage` 簡略化 |
| 04 Onboarding設計 | `questions.yaml` 外部化、既存資料回答省略対応 |
| 05 保存・セキュリティ設計 | 同一ディレクトリ一時ファイルによるアトミック書き込み、4層承認保護、ロックファイル廃止（revision+SHA-256競合検出） |
| 06 Skills契約 | 11スキルのI/O契約定義（MVP/P1優先度付き） |
| 07 テスト計画 | AT-01〜AT-10 受入試験定義、AT-10 Lite（Phase 2 Codex最小検証）追加 |
| 08 実装計画 | Phase 2〜7ロードマップ、Phase 2タスク15本の詳細計画 |
| 09 未決事項 | OI-01〜OI-13、AS-01〜AS-05、R-01〜R-06を記録 |

**運用方針確定**
- プロジェクトルートに `CLAUDE.md` を作成（Claude Code自律実施範囲・承認事項・報告方式を規定）

### 承認された主要決定

| 決定事項 | 内容 |
|---------|------|
| Codex対象 | OpenAI Codex（VS Code）、公式仕様基準で互換化 |
| データ保存先 | `exhibition-production-data/` を製品本体と分離 |
| Skills管理 | `core/skills/` 単一ソース、アダプターが各環境にデプロイ |
| バリデーション | pydantic v2、JSON Schemaは自動生成 |
| 設定方式 | `deployment.yaml`（gitignore）＋ `deployment.yaml.template`（Git管理） |
| 競合検出 | ロックファイル廃止、revision番号＋SHA-256ハッシュで検出 |
| 質問管理 | `questions.yaml` 外部定義、既存資料での事前回答省略可 |

### 未解決で次Phaseに持越し

- OI-01: プロジェクトレベルスキル配置の動作確認（Phase 2実装前）
- OI-11: Codex固有のSkills/Tools実行機構の有無（Phase 2初期タスク2-11）
- OI-02: Codex AGENTS.mdの文字数制限（Phase 2初期、OI-11と同時）

---

<!-- 以降、各作業完了後に追記 -->
