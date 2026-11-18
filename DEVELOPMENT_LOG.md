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

---

## 2026-11-18 ── Phase 2 実装

### タスク 2-00〜2-10：環境構築・共通基盤

**作成ファイル（61ファイル、初回コミット `c7d653f`）:**

| カテゴリ | 主なファイル |
|---------|------------|
| プロジェクト設定 | `.gitignore`、`.gitattributes`、`deployment.yaml.template`、`pyproject.toml`、`requirements.txt` |
| Pydantic モデル（9件） | `core/models/{museum_profile,profile_evidence,onboarding_session,...}.py` |
| コアモジュール | `core/storage.py`（アトミック書き込み・競合検出）、`core/integrity.py`（SHA-256）、`core/audit.py`、`core/config.py`（4階層設定） |
| スクリプト | `scripts/generate_schemas.py`、`scripts/deploy.py` |
| アダプター | `adapters/claude-code/`、`adapters/codex/`（スケルトン） |
| 設定 YAML | `core/policies/common-settings.yaml`、4ドメインの `domain-settings.yaml` |
| テスト | `tests/unit/test_storage.py`（17件）、`tests/unit/test_integrity.py`（8件） |

**スキーマ生成:** `python scripts/generate_schemas.py` → 9件の `.schema.json` を `schemas/` に出力

### タスク 2-11：Codex Skills 仕様調査（OI-02・OI-11 解決）

**OI-11 確定:**
- Codex は **Agent Skills open standard**（agentskills.io）をサポート
- SKILL.md フォーマットは Claude Code と共通（Anthropic が開発・公開、2025年12月）
- 配置先のみ異なる: Claude Code = `.claude/skills/`、Codex = `.agents/skills/`
- `adapters/codex/generate-skills.py` を実装（`core/skills/` → `.agents/skills/` のコピー）

**OI-02 確定:**
- AGENTS.md 上限 32 KiB（本プロジェクトの推定サイズ ~7KB、余裕あり）

### タスク 2-12：OI-01 検証（プロジェクトレベルスキル配置）

- テストスキル `.claude/skills/exhibition-oi01-test/SKILL.md` を配置済み
- 次回セッション開始時に `/exhibition-oi01-test` で動作確認する
- 確認後にテストスキルを削除する

### テスト結果

```
pytest tests/unit/ → 25 passed in 0.40s （全件合格）
```

### 未解決で Phase 3 に持越し

- OI-01: プロジェクトレベルスキル配置の実動作確認（次回セッション）
- OI-04: デプロイスクリプトの実行タイミング（Phase 3設計時）
- OI-13: `questions.yaml` フォーマット仕様確定（Phase 3実装前）

<!-- 以降、各作業完了後に追記 -->
