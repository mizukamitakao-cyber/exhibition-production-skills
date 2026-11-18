# 02 アーキテクチャ設計

文書日：2026年11月18日（Rev.2 2026年11月18日）  
文書区分：Phase 1 アーキテクチャ設計  
ステータス：Phase 1確定

---

## 1. システム概要

製品リポジトリと館別データ領域を物理的に分離した2領域構成を基本とする。

```
Documents/
├── exhibition-production-skills/   ← 製品リポジトリ（Git管理）
│   共通Skills・スキーマ・ナレッジ・テンプレート・アダプター
│
└── exhibition-production-data/     ← 館別データ領域（Git管理は任意）
    各館の設定・調査資料・展示案件
```

**分離の目的：**
- 製品更新が館別データを上書きしない
- 館別データを製品リポジトリから独立して管理・バックアップできる
- 将来、複数館に同一製品を配布できる

---

## 2. 製品リポジトリの構成

```
exhibition-production-skills/
├── .claude/
│   └── CLAUDE.md                     # プロジェクト固有指示（Claude Code用）
│
├── core/
│   ├── skills/                       # Skillsの単一ソース（§5参照）
│   │   ├── exhibition-deployment-setup/
│   │   ├── exhibition-museum-onboarding/
│   │   ├── exhibition-director/
│   │   ├── exhibition-idea-generator/
│   │   ├── exhibition-researcher/
│   │   ├── exhibition-planner/
│   │   ├── exhibition-story-designer/
│   │   ├── exhibition-writer/
│   │   ├── exhibition-visual-designer/
│   │   ├── exhibition-advocate/
│   │   └── exhibition-reviewer/
│   ├── workflows/                    # ワークフロー定義（YAML）
│   ├── policies/
│   │   └── common-settings.yaml     # 共通安全制約（全館・全案件に適用、上書き不可）
│   └── knowledge/                   # 共通・専門分野別ナレッジ（§4の第1・2層）
│       ├── common/                  # 全分野共通の展示制作手法・品質基準
│       └── domains/                 # 専門分野別設定・ナレッジ
│           ├── history/
│           │   └── domain-settings.yaml
│           ├── art/
│           │   └── domain-settings.yaml
│           ├── natural-history/
│           │   └── domain-settings.yaml
│           └── science/
│               └── domain-settings.yaml
│
├── adapters/
│   ├── claude-code/
│   │   ├── deploy.py                 # core/skills → ~/.claude/skills/ インストール
│   │   └── CLAUDE.md.template        # プロジェクト設定テンプレート
│   └── codex/
│       ├── generate-instructions.py  # core/skills → AGENTS.md 変換（指示層）
│       ├── AGENTS.md.base            # Codex用の基本指示テンプレート
│       ├── generate-skills.py        # core/skills → Codex Skills形式 変換（実行層）
│       │                             # ← Phase 2調査後に設計・実装
│       └── README.md                 # Codex互換性の調査結果・設計方針
│
├── schemas/                          # Pydanticモデルから自動生成（手動管理しない）
│   └── *.schema.json                 # scripts/generate_schemas.py が出力
│
├── templates/                        # 成果物テンプレート
│   ├── exhibition-plan.md
│   ├── story-structure.md
│   └── ...
│
├── scripts/
│   ├── deploy.py                     # 統合デプロイスクリプト
│   └── generate_schemas.py           # Pydanticモデルから JSON Schema を自動生成
│
├── tests/
│   ├── unit/
│   └── acceptance/
│       └── test-data/                # 架空テスト館データ（git管理）
│
├── deployment.yaml.template          # deployment.yaml のテンプレート（git管理）
├── .gitignore                        # deployment.yaml・生成物を除外
└── docs/
    ├── design/                       # Phase 1設計文書
    └── ...
```

---

## 3. 館別データ領域の構成

```
exhibition-production-data/         # パスはdeployment.yamlで設定（場所は自由）
└── museums/
    └── {museum-id}/
        ├── profile/
        │   ├── museum-profile-v1.yaml         # 承認済み館別プロファイル（版管理）
        │   ├── museum-profile-draft.yaml      # 編集中の下書き
        │   └── _backup/                       # 旧バージョン・承認前ドラフト保管
        ├── knowledge/                         # 館別ナレッジ（方針・規程等）
        ├── source-materials/                  # 調査資料（許諾済みのみ）
        ├── idea-bank/                         # 企画アイディア蓄積
        ├── projects/
        │   └── {project-id}/
        │       ├── project.yaml               # 案件メタデータ（§4の第4層設定）
        │       ├── artifact-manifest.yaml
        │       ├── ideas/
        │       ├── research/
        │       ├── plan/
        │       ├── story/
        │       ├── manuscripts/
        │       ├── design/
        │       └── reviews/
        └── system/
            └── operation-log.yaml             # 監査ログ（追記型）
```

---

## 4. 設定の4階層構造

設定は以下の4階層で管理する。**下位設定が上位設定より優先**されるが、**上位の安全制約は下位から解除できない。**

| 階層 | 設定ファイル | 保存場所 | 優先度 | 安全制約 |
|------|-----------|---------|--------|---------|
| ① 共通設定 | `core/policies/common-settings.yaml` | 製品リポジトリ | 最低 | **解除不可** |
| ② 専門分野別設定 | `core/knowledge/domains/{domain}/domain-settings.yaml` | 製品リポジトリ | 低 | 共通制約の範囲内 |
| ③ 館別設定 | `{museum-id}/profile/museum-profile-vN.yaml` | 館別データ領域 | 高 | ①②制約の範囲内 |
| ④ 案件別設定 | `{project-id}/project.yaml` の `brief.*` | 館別データ領域 | 最高 | ①②③制約の範囲内 |

**上書き不可の共通安全制約（例）：**
- 架空の出典・引用を作成しない
- 確認済み事実とAI推論を区別する
- 個人情報をAIへ入力しない
- 承認済み成果物を無断で変更しない
- `data_root` 外へのファイル書き込みを禁止する

**設定の解決順序：**  
Skillsが設定値を参照する際は、`④案件別 → ③館別 → ②専門分野別 → ①共通` の順で確認し、安全制約に違反しない範囲で下位設定を採用する。

---

## 5. Skillsの単一ソース管理

**設計原則：同一内容を2箇所に管理しない。**

`core/skills/` を唯一の正本とし、各AI実行環境への配布はアダプターが担う。

```
core/skills/<skill-name>/
├── SKILL.md          # スキル定義（Claude Code SKILL.md形式）
├── README.md         # スキルの説明・使い方
├── references/       # 実行時にコンテキスト注入される参照文書
│   ├── function-*.md
│   └── ...
└── templates/        # このスキルが生成する成果物のテンプレート
    └── *.template.yaml / *.template.md
```

### 5.1 Claude Code アダプター

`adapters/claude-code/deploy.py` が実行する処理：
1. `core/skills/` 配下の全スキルを読み込む
2. `~/.claude/skills/` または `.claude/skills/`（プロジェクトレベル、OI-01検証）にコピー
3. インストール結果をログに記録

デプロイ先（`~/.claude/skills/` または `.claude/skills/`）はGit管理外。製品リポジトリの `.gitignore` に `.claude/skills/` を追加する。

### 5.2 Codex アダプター（2層構造）

Codex対応は **指示層** と **スキル実行層** の2層で構成する。

**層1：指示層（AGENTS.md）**  
Claude CodeにおけるCLAUDE.mdに相当するプロジェクト指示ファイル。

`adapters/codex/generate-instructions.py` が実行する処理：
1. `core/skills/` 配下の全スキルのSKILL.mdを読み込む
2. `AGENTS.md.base` のテンプレートに展開してマージ
3. `AGENTS.md` を製品リポジトリのルートに生成（Git管理外）

**層2：スキル実行層（Codex Skills）**  
Claude CodeにおけるSKILL.mdのスキル実行機構に相当する。CodexがSKILL.md形式と異なるネイティブのスキル機構を持つ場合に実装する。

`adapters/codex/generate-skills.py`：  
Phase 2初期にCodex Skillsの公式仕様を確認した後に設計・実装する（OI-02）。

**現時点の設計判断：**  
- 「AGENTS.md生成のみ = Codex対応完了」とは扱わない
- Codex Skillsの仕様調査なしにアダプター設計を確定しない
- Phase 2調査結果を `adapters/codex/README.md` に記録し、設計方針を確定する

---

## 6. プロジェクト設定ファイル

### 6.1 .claude/CLAUDE.md（Claude Code用）

プロジェクト固有の動作指示を定義する（Git管理）。主な内容：
- 本プロジェクトの目的と作業範囲
- `deployment.yaml` の読み込みルール
- 館別データへのアクセス方法
- 承認・保存に関する安全ルール（`core/policies/` 参照）
- スキルの自動トリガー条件

### 6.2 AGENTS.md（Codex用）

`adapters/codex/generate-instructions.py` が生成する（Git管理外）。主な内容：
- 全Skillsの指示をセクションとして統合
- 館別データのアクセスルール
- 承認・保存ルール

指示層のみ。Codex Skillsの実行機構はPhase 2調査後に追加する。

### 6.3 deployment.yaml（導入先固有設定）

**2ファイル構成（テンプレートと実設定を分離）：**

```
deployment.yaml.template   ← Git管理（テンプレート・記入例付き）
deployment.yaml            ← Git管理外（.gitignoreに記載）
```

**deployment.yaml.template の内容：**
```yaml
# deployment.yaml.template
# コピーして deployment.yaml として保存してください
# deployment.yaml は .gitignore に含まれます（Git管理外）
#
# ⚠ 秘密情報（APIキー・パスワード・トークン）をこのファイルに書かないでください
#    認証情報が必要な場合は環境変数を使用してください（例: $env:MY_API_KEY）

product_version: ""       # 例: "1.0.0"（導入製品バージョンの追跡に使用）
museum_id: ""             # 例: "natural-history-museum-001"
data_root: ""             # 例: "C:/Users/.../exhibition-production-data"
                          # Windows: バックスラッシュではなくスラッシュを使用
```

**`.gitignore` に含めるもの：**
```gitignore
deployment.yaml           # 導入先固有設定（Git管理外）
AGENTS.md                 # Codexアダプターの生成物
.claude/skills/           # Claude Codeデプロイ先（Git管理外）
schemas/*.schema.json     # Pydantic自動生成物（再生成可能）
*.secret
*.key
```

---

## 7. コンポーネント責務の概要

| コンポーネント | 責務 | 実装形式 |
|-------------|------|---------|
| `core/skills/` | Skillsの定義・指示（単一ソース） | Markdown（SKILL.md形式） |
| `core/workflows/` | Skillsの実行順序・連携フロー | YAML |
| `core/policies/common-settings.yaml` | 全館共通の安全制約（上書き不可） | YAML |
| `core/knowledge/common/` | 全分野共通の展示制作手法・品質基準 | Markdown/YAML |
| `core/knowledge/domains/` | 専門分野別設定・ナレッジ | YAML/Markdown |
| `adapters/claude-code/` | Claude Codeへのデプロイ | Python script |
| `adapters/codex/` | Codex向けAGENTS.md生成（指示層）＋Skills変換（実行層、Phase 2設計） | Python script |
| `schemas/` | Pydanticモデルから自動生成したJSON Schema（再生成可能） | JSON Schema |
| `templates/` | 成果物の出力テンプレート | Markdown/YAML |
| `scripts/deploy.py` | 統合デプロイ（アダプター呼び出し） | Python script |
| `scripts/generate_schemas.py` | Pydanticモデル → JSON Schema の自動生成 | Python script |
| `tests/` | 動作検証・受入試験 | Python + 架空テストデータ |

---

## 8. 主要設計決定事項

| 決定事項 | 採用方針 | 理由 |
|---------|---------|------|
| スキル形式 | Claude Code形式（SKILL.md）を単一ソースとする | 先行開発環境に合わせる。Codexはアダプターで対応 |
| Codex対応 | AGENTS.md（指示層）とCodex Skills（実行層）の2層構造。実行層はPhase 2調査後に確定 | AGENTS.mdのみでCodex対応が完了する前提を置かない |
| 設定4階層 | 共通→専門分野別→館別→案件別。上位の安全制約は下位から解除不可 | v0.3 §5.3の要件に基づく |
| Windowsシンボリックリンク | 使用しない | 管理者権限が必要で開発者環境に依存するため |
| スキル名プレフィックス | `exhibition-` を付与 | 既存スキルとの名前衝突を防ぐため |
| 館別データパス | `deployment.yaml` で設定可能（導入先ごとに自由に設定） | 導入先ごとに異なるパスを許容するため |
| deployment.yaml | テンプレート（Git管理）と実設定（Git管理外）を分離。秘密情報不可 | 個人パス・機密情報のGit混入を防ぐため |
| JSON Schema管理 | Pydanticモデルから自動生成。手動メンテ不要 | モデルとスキーマの二重管理を避けるため |
| Git管理範囲 | 製品リポジトリのみ必須。館別データは任意 | 顧客データと製品コードを分離するため |
