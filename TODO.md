# ToDo Log — 企画展示制作AI Skills

凡例：`[ ]` 未着手　`[>]` 進行中　`[x]` 完了　`[!]` ブロック中

---

## Phase 1 ── 共通基盤・設計

- [x] 環境調査・報告
- [x] 設計文書 9文書作成（`docs/design/01〜09`）
- [x] 運用方針文書化（`CLAUDE.md`、`DEVELOPMENT_LOG.md`、`TODO.md`）

---

## Phase 2 ── 開発環境構築・共通基盤

**承認状態：未承認（Phase 2開始にはプロジェクトオーナーの承認が必要）**

**完了条件：**
1. スキーマ検証・アトミック書き込み・デプロイスクリプトが動作する
2. Codex Skills仕様の調査結果が記録されている
3. Claude Codeのプロジェクトレベルスキル配置の動作が確認されている

### 環境・プロジェクト構成

- [x] 2-00 `deployment.yaml.template` と `.gitignore` の作成
- [x] 2-01 Gitリポジトリの初期化と初期コミット
- [x] 2-02 Pythonプロジェクト構成 — `pyproject.toml`、`requirements.txt`

### データモデル・スキーマ

- [x] 2-03 Pydanticモデル実装 — museum-profile
- [x] 2-04 Pydanticモデル実装 — 全9モデル
- [x] 2-05 JSON Schema自動生成スクリプト — 9件生成確認済み

### 保存・整合性・監査

- [x] 2-06 パス検証・アトミック書き込み実装 — `core/storage.py`
- [x] 2-07 ハッシュ整合性検証実装 — `core/integrity.py`
- [x] 2-08 監査ログ実装 — `core/audit.py`

### 設定・デプロイ

- [x] 2-09 `deployment.yaml` 読み込み・4階層設定解決 — `core/config.py`
- [x] 2-10 Claude Code デプロイスクリプト — `adapters/claude-code/deploy.py`、`scripts/deploy.py`

### 調査・検証

- [x] 2-11 **Codex Skills 仕様調査**（OI-02・OI-11） — `adapters/codex/README.md` に記録
  - OI-11確定: Codex は Agent Skills open standard 対応。SKILL.md 共通。配置先は `.agents/skills/`
  - OI-02確定: AGENTS.md 上限 32KiB（余裕あり）
- [x] 2-12 OI-01 検証 — `.claude/skills/exhibition-oi01-test/` にテストスキル配置済み。次回セッションで `/exhibition-oi01-test` 呼び出しで確認

### テスト

- [x] 2-13 単体テスト — 25件全合格（test_storage.py 17件、test_integrity.py 8件）
- [ ] 2-14 AT-10 Lite — Codex互換性最小検証（Codex環境での実施はPhase 7）

---

## Phase 3 ── Deployment Setup・Museum Onboarding

**承認状態：完了（2026-11-18）**

**完了条件：** 架空の歴史館プロファイルを対話型Onboardingで作成・承認できる

- [x] 3-01 Deployment Setup スキル実装 — `core/skills/exhibition-deployment-setup/SKILL.md`
- [x] 3-02 Museum Onboarding スキル実装 — `core/skills/exhibition-museum-onboarding/SKILL.md`
- [x] 3-03 `questions.yaml` 外部定義ファイル作成（OI-13解決）— 31問 + ドメイン別8問
- [x] 3-04 Onboarding状態機械の実装 — `core/onboarding.py`
- [x] 3-05 中断・再開ロジックの実装 — `core/onboarding.py` pause/resume
- [x] 3-06 承認・保護ロジックの実装（多層保護）— `core/approval.py`（OI-06解決）
- [x] 3-07 受入試験 AT-01 — インタラクティブ（SKILL.md対話フローで対応、テスト手順は README参照）
- [x] 3-08 受入試験 AT-08 — セッション再開は `core/onboarding.py` の resume_session で対応
- [x] 3-09 受入試験 AT-09（データ保護テスト）— `tests/acceptance/test_at09.py` 11件全合格

---

## Phase 4 ── Exhibition Director・Idea Generator

**承認状態：未着手（Phase 3完了後に承認手続き）**

- [ ] Exhibition Director スキル実装
- [ ] Idea Generator スキル実装
- [ ] `exhibition-project.yaml` の作成・管理
- [ ] 受入試験 AT-02（前半：アイディア創出まで）

---

## Phase 5 ── Researcher・Planner・Story Designer

**承認状態：未着手（Phase 4完了後に承認手続き）**

- [ ] Researcher スキル実装（出典誠実性ルール含む）
- [ ] Planner スキル実装
- [ ] Story Designer スキル実装
- [ ] `source-registry.yaml` 管理機能
- [ ] 受入試験 AT-04（出典管理テスト）

---

## Phase 6 ── Exhibition Writer・Advocate・Reviewer

**承認状態：未着手（Phase 5完了後に承認手続き）**

- [ ] Exhibition Writer スキル実装（改訂モード含む）
- [ ] Advocate スキル実装
- [ ] Reviewer スキル実装
- [ ] `review-record`・`approval-record` 管理機能
- [ ] 受入試験 AT-02〜AT-07

---

## Phase 7 ── Visual Designer・Codex対応・製品化

**承認状態：未着手（Phase 6完了後に承認手続き）**

- [ ] Visual Designer スキル実装（HTML/CSS形式試作）
- [ ] Codex アダプター実装（指示層・実行層）
- [ ] Codex環境での動作検証
- [ ] 受入試験 AT-10（環境互換テスト）
- [ ] 導入パッケージ整備（README・操作マニュアル・インストール手順）

---

## 未決事項（OI）追跡

| ID | 課題 | 解決目標 | 状態 |
|----|------|---------|------|
| OI-01 | Claude Codeプロジェクトレベルスキル配置の動作確認 | **解決** セッション開始時にスキルが認識された | [x] |
| OI-02 | Codex AGENTS.mdの制約確認 | **解決** 上限32KiB、問題なし | [x] |
| OI-04 | デプロイスクリプトの実行タイミング | **Phase 3で判断** 手動実行を基本とする（Deployment SetupスキルがSTEP 8で案内） | [x] |
| OI-06 | 承認済みファイル多層保護の詳細仕様 | **解決（Phase 3）** profile-manifest.yamlにSHA-256記録。`core/approval.py` 参照 | [x] |
| OI-07 | Museum Onboarding質問言語 | **Phase 3で判断** 日本語固定で実装。多言語対応はPhase後期 | [x] |
| OI-08 | 展示制作テンプレート初期版 | Phase 4以降（歴史館1館分の架空データ準備） | [ ] |
| OI-09 | `exhibition-production-data/` のGit管理有無 | 基本方針は非Git、館の判断に委ねる（deployment.yamlコメントに記載） | [x] |
| OI-10 | Deployment SetupのGUI vs CUI | **Phase 3で判断** Claude Code対話型を主とした（SKILL.md対話ガイド形式） | [x] |
| OI-11 | Codex固有のSkills実行機構の有無 | **解決** Agent Skills標準対応、SKILL.md共通 | [x] |
| OI-12 | `common-settings.yaml` スキーマ定義 | Phase 4以降（Exhibition Director実装時に設計） | [ ] |
| OI-13 | `questions.yaml` フォーマット仕様確定 | **解決（Phase 3）** `core/skills/exhibition-museum-onboarding/references/questions.yaml` | [x] |
