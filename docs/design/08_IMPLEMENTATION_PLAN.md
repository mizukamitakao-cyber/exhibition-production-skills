# 08 実装計画（Phase 2以降）

文書日：2026年11月18日（Rev.2 2026年11月18日）  
文書区分：Phase 1 実装計画  
ステータス：Phase 1確定

---

## 1. 実装の基本方針

| 方針 | 内容 |
|------|------|
| MVP優先 | P0機能を最初に完成させ、動作確認後にP1へ進む |
| 設計→実装→受入試験のサイクル | 各Phaseは詳細設計→レビュー→実装→受入試験で完結する |
| アーキテクチャ優先 | 共通基盤（スキーマ・保存・検証）を先行し、Skills実装を後続にする |
| 過剰実装の禁止 | 各PhaseはそのPhaseの完了条件のみを実装する |
| テストデータ | 架空の3館（歴史・美術・自然史）を使用する |
| 単一書き込み主体 | MVPでは同一館別データへの同時書き込みは発生しない前提で運用する |

---

## 2. 開発ロードマップ

| Phase | 開発内容 | 完了目標 | 前提条件 |
|-------|---------|---------|---------|
| **1** | 共通基盤・設計 | 設計文書確定 | — |
| **2** | 開発環境構築・共通基盤 | デプロイ・スキーマ・保存が動作する | Phase 1承認 |
| **3** | Deployment Setup・Museum Onboarding | 館別プロファイルを作成・承認できる | Phase 2完了 |
| **4** | Exhibition Director・Idea Generator | 対話型企画検討ができる | Phase 3完了 |
| **5** | Researcher・Planner・Story Designer | 出典付き企画書・構成表を作成できる | Phase 4完了 |
| **6** | Exhibition Writer・Advocate・Reviewer | 原稿制作・改訂・品質検証ができる | Phase 5完了 |
| **7** | Visual Designer・Codex対応・製品化 | 編集可能試作と複数環境対応ができる | Phase 6完了 |

---

## 3. Phase 2 詳細計画（開発環境構築・共通基盤）

**完了条件：**
- スキーマ検証・アトミック書き込み・デプロイスクリプトが動作する
- Codex Skills仕様の調査結果が記録されている
- Claude Codeのプロジェクトレベルスキル配置の動作が確認されている

### タスク一覧

| # | タスク | 成果物 | 依存 |
|---|--------|--------|------|
| 2-00 | `deployment.yaml.template` と `.gitignore` の作成 | `deployment.yaml.template`、`.gitignore` | — |
| 2-01 | Gitリポジトリの初期化と初期コミット | `.git/`、初期コミット | 2-00 |
| 2-02 | Pythonプロジェクト構成 | `pyproject.toml`、`requirements.txt`（`pydantic>=2`、`ruamel.yaml`） | 2-01 |
| 2-03 | Pydanticモデル実装（museum-profile） | `core/models/museum_profile.py` | 2-02 |
| 2-04 | Pydanticモデル実装（全9モデル） | `core/models/*.py` | 2-03 |
| 2-05 | JSON Schema自動生成スクリプト | `scripts/generate_schemas.py`、`schemas/*.schema.json` | 2-04 |
| 2-06 | パス検証・アトミック書き込み実装 | `core/storage.py` | 2-02 |
| 2-07 | ハッシュ整合性検証実装 | `core/integrity.py` | 2-06 |
| 2-08 | 監査ログ実装 | `core/audit.py` | 2-06 |
| 2-09 | `deployment.yaml` 読み込み・4階層設定解決の実装 | `core/config.py` | 2-02 |
| 2-10 | Claude Code デプロイスクリプト | `adapters/claude-code/deploy.py`、`scripts/deploy.py` | 2-09 |
| 2-11 | **Codex Skills 仕様調査**（OI-02） | `adapters/codex/README.md`（調査結果・設計方針） | 2-10 |
| 2-12 | OI-01 検証（プロジェクトレベルスキル配置） | 検証メモ、方針確定 | 2-10 |
| 2-13 | 単体テスト実装（2-06、2-07対象） | `tests/unit/test_storage.py`、`tests/unit/test_integrity.py` | 2-07 |
| 2-14 | AT-10 Lite（Codex互換性最小検証） | テスト合格記録 | 2-11 |

**タスク2-11の内容（Codex Skills仕様調査）：**  
Phase 2初期にOpenAI Codex VS Codeの公式ドキュメントを確認し、以下を明らかにする：
1. Codex固有のSkills/Tools実行機構が存在するか
2. 存在する場合、SKILL.md形式との対応関係
3. AGENTS.md（指示層）とSkills実行層の役割分担の最終設計
4. 調査結果を `adapters/codex/README.md` に記録し、Codexアダプターの設計方針を確定する

**主要リスク：**
- OI-01（プロジェクトレベルスキル配置）の結果によりデプロイ方式が変わる
- Codex Skills調査の結果によりアダプター設計に変更が必要になる可能性がある

---

## 4. Phase 3 詳細計画（Deployment Setup・Museum Onboarding）

**完了条件：** 架空の歴史館プロファイルを対話型Onboardingで作成・承認できる

### タスク一覧

| # | タスク | 成果物 | 依存 |
|---|--------|--------|------|
| 3-01 | Deployment Setup スキル実装 | `core/skills/exhibition-deployment-setup/` | Phase 2完了 |
| 3-02 | Museum Onboarding スキル実装 | `core/skills/exhibition-museum-onboarding/` | Phase 2完了 |
| 3-03 | `questions.yaml` 外部定義ファイル作成 | `core/skills/exhibition-museum-onboarding/references/questions.yaml` | 3-02 |
| 3-04 | Onboarding状態機械の実装 | `core/onboarding.py` | Phase 2完了 |
| 3-05 | 中断・再開ロジックの実装 | `core/onboarding.py`（更新） | 3-04 |
| 3-06 | 承認・保護ロジックの実装（多層保護） | `core/approval.py` | Phase 2完了 |
| 3-07 | 受入試験 AT-01（館別設定テスト） | テスト合格記録 | 3-02 |
| 3-08 | 受入試験 AT-08（セッション再開テスト） | テスト合格記録 | 3-05 |
| 3-09 | 受入試験 AT-09（データ保護テスト） | テスト合格記録 | 3-06 |

**主要リスク：**
- 質問フローが長すぎてユーザーが離脱するリスク → フェーズ単位での中断を必ず実装する
- `questions.yaml` の外部化により動的読み込みの実装が必要になる

---

## 5. Phase 4〜7 概要計画

### Phase 4：Exhibition Director・Idea Generator

**完了条件：** Director主導の対話で案件を作成し、アイディアを生成・選定できる

主要タスク：
- Exhibition Director スキル実装
- Idea Generator スキル実装
- `exhibition-project.yaml` の作成・管理
- 受入試験 AT-02（前半：アイディア創出まで）

---

### Phase 5：Researcher・Planner・Story Designer

**完了条件：** 出典付き企画書と展示構成表を作成できる

主要タスク：
- Researcher スキル実装（出典誠実性ルールの実装を含む）
- Planner スキル実装
- Story Designer スキル実装
- `source-registry.yaml`（`source_usage` 含む）の管理機能
- 受入試験 AT-04（出典管理テスト）

---

### Phase 6：Exhibition Writer・Advocate・Reviewer

**完了条件：** 原稿制作・改訂・品質検証の完全サイクルが動作する

主要タスク：
- Exhibition Writer スキル実装（改訂モード含む）
- Advocate スキル実装
- Reviewer スキル実装
- `review-record`・`approval-record` の管理機能
- 受入試験 AT-02〜AT-07（各テストケース完了）

---

### Phase 7：Visual Designer・Codex対応・製品化

**完了条件：** 複数環境での導入・更新・運用ができる

主要タスク：
- Visual Designer スキル実装（HTML/CSS形式の試作）
- Codex アダプター Phase 2設計に基づく実装
  - `adapters/codex/generate-instructions.py`（指示層）
  - `adapters/codex/generate-skills.py`（スキル実行層、仕様確定後）
- Codex環境での動作検証
- 受入試験 AT-10（環境互換テスト）
- 導入パッケージの整備（README・操作マニュアル・インストール手順）

---

## 6. 全体の依存関係

```
Phase 2（基盤）
    └→ Phase 3（Onboarding）
           └→ Phase 4（Director・Idea）
                  └→ Phase 5（Research・Plan・Story）
                         └→ Phase 6（Writer・Advocate・Reviewer）
                                └→ Phase 7（Visual・Codex・製品化）
```

各Phaseは前Phaseの受入試験合格を開始条件とする。

---

## 7. 全体リスクと対応

| リスク | Phase | 対応策 |
|--------|-------|--------|
| Codex Skills仕様調査でアダプター設計の大幅見直しが必要になる | 2 | Phase 2調査後に`adapters/codex/`設計を確定。Phase 7実装に影響しない構造を維持 |
| Skillsの対話品質が実務に合わない | 3〜6 | 架空館での早期試用、担当者フィードバックを逐次反映 |
| 承認フローが実際の業務フローと合わない | 3〜5 | 承認段階はプロファイルで柔軟に設定できる設計にする |
| 出典管理の粒度が粗すぎる | 5 | Phase 5設計時に担当者の実務水準に合わせて調整する |
| 製品化要件（ライセンス・マニュアル）の未定義 | 7 | Phase 7設計時に別途要件定義する |
