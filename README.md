# 企画展示制作 AI Skills

博物館・文書館の **展示制作業務をAIで支援する** Claude Code / Codex 向けスキルシステムです。

企画立案から調査・原稿執筆・デザイン試作まで、展示制作の全工程を 11 のスキルでカバーします。
データはすべてローカルに保存され、外部サービスへの送信は行いません。

---

## 目次

1. [スキル一覧](#スキル一覧)
2. [前提条件](#前提条件)
3. [インストール手順](#インストール手順)
4. [使い方（クイックスタート）](#使い方クイックスタート)
5. [データ構造](#データ構造)
6. [Codex（VS Code）での利用](#codexvs-codeでの利用)
7. [開発者向け情報](#開発者向け情報)

---

## スキル一覧

| スキル名 | 呼び出し方 | 主な機能 |
|---------|-----------|---------|
| `exhibition-deployment-setup` | `/exhibition-deployment-setup` | 初回セットアップ・deployment.yaml 作成 |
| `exhibition-museum-onboarding` | `/exhibition-museum-onboarding` | 館別プロファイル（方針・制約）の作成・承認 |
| `exhibition-director` | `/exhibition-director` | 展示案件の新規作成・管理 |
| `exhibition-idea-generator` | `/exhibition-idea-generator` | 展示テーマ・コンセプトのアイディア生成・選定 |
| `exhibition-researcher` | `/exhibition-researcher` | 調査メモ・出典台帳の管理（架空出典禁止ルール付き）|
| `exhibition-planner` | `/exhibition-planner` | 展示企画書の作成・承認管理 |
| `exhibition-story-designer` | `/exhibition-story-designer` | 展示構成表（章立て・セクション設計）の作成 |
| `exhibition-writer` | `/exhibition-writer` | パネル・キャプション等の原稿執筆・改訂 |
| `exhibition-advocate` | `/exhibition-advocate` | 成果物の批判的検討（5観点・改善提案） |
| `exhibition-reviewer` | `/exhibition-reviewer` | 要件検証（文字数・出典・表記・形式） |
| `exhibition-visual-designer` | `/exhibition-visual-designer` | パネルのHTML/CSSレイアウト試作生成 |

---

## 前提条件

| 要件 | バージョン |
|------|-----------|
| Python | 3.11 以上 |
| Claude Code | 最新版（`npm install -g @anthropic-ai/claude-code`） |
| pydantic | 2.x |
| ruamel.yaml | 0.18 以上 |

---

## インストール手順

### 1. リポジトリのクローン

```bash
git clone <このリポジトリのURL>
cd exhibition-production-skills
```

### 2. Python 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

または

```bash
pip install -e .
```

### 3. Claude Code へのスキルデプロイ

```bash
python scripts/deploy.py
```

このコマンドが `core/skills/` 配下の全スキルを `~/.claude/skills/` にコピーします。

### 4. deployment.yaml の作成

プロジェクトルートに `deployment.yaml` を作成します：

```yaml
data_root: /path/to/your/exhibition-production-data
museum_id: your-museum-id
```

> **ヒント**: テンプレートが `deployment.yaml.template` にあります。

---

## 使い方（クイックスタート）

### Step 1: 初回セットアップ

```
/exhibition-deployment-setup
```

`deployment.yaml` の作成と動作確認を行います。

### Step 2: 館別プロファイルの作成

```
/exhibition-museum-onboarding
```

館の方針・来館者層・文字数制限などをヒアリング形式で記録します。
作成後は承認が必要です（承認済みプロファイルは保護されます）。

### Step 3: 展示案件の作成

```
/exhibition-director
```

展示タイトル・テーマ・会期等を設定して案件を作成します。

### Step 4: アイディアの生成・選定

```
/exhibition-idea-generator
```

展示コンセプトのアイディアを3〜5件生成し、担当者が選定します。

### Step 5: 調査・企画書作成

```
/exhibition-researcher   ← 調査メモ・出典の登録
/exhibition-planner      ← 展示企画書の作成
/exhibition-story-designer  ← 展示構成表の作成
```

### Step 6: 原稿執筆・品質検証

```
/exhibition-writer    ← パネル原稿の執筆
/exhibition-advocate  ← 批判的検討（論理・来館者視点）
/exhibition-reviewer  ← 要件検証（文字数・出典）
```

### Step 7: デザイン試作

```
/exhibition-visual-designer
```

承認済み原稿からHTML/CSSパネルレイアウトの試作を生成します。
`design/panel-{panel_id}.html` をブラウザで確認できます。

---

## データ構造

```
{data_root}/
  {museum_id}/
    museum-profile-v{N}.yaml   ← 館別プロファイル（承認済みは読み取り専用）
    profile-manifest.yaml      ← プロファイル整合性ハッシュ
    {project_id}/
      exhibition-project.yaml  ← 案件情報
      ideas/
        idea-list.yaml          ← アイディア一覧
        comparison.md           ← アイディア比較表
      research/
        source-registry.yaml   ← 出典台帳
        memo-{id}.md            ← 調査メモ
      plan/
        artifact-manifest.yaml  ← 成果物管理台帳
        exhibition-plan-v{N}.md ← 展示企画書
      story/
        story-structure-v{N}.yaml  ← 展示構成表
        story-structure-v{N}.md    ← 展示構成表（Markdown）
      manuscripts/
        {panel_id}-v{N}.md     ← パネル原稿
      reviews/
        review-{id}.yaml       ← レビュー記録
        approval-{id}.yaml     ← 承認記録
      design/
        panel-{panel_id}.html  ← HTMLレイアウト試作
        concept.md             ← デザインコンセプトメモ
```

### バージョン管理の原則

- **原本は上書きしない**: 改訂版は必ず新しいバージョン番号（v1→v2）で保存します
- **承認済みファイルは保護**: SHA-256ハッシュによる整合性検証
- **audit ログ**: 主要な操作はすべて `audit.log` に記録されます

---

## Codex（VS Code）での利用

Codex でこのシステムを使用するには、以下のコマンドでスキルをデプロイします：

```bash
# プロジェクトスコープ（チーム共有）
python adapters/codex/generate-skills.py project

# ユーザースコープ（個人利用）
python adapters/codex/generate-skills.py user
```

Codex 向けの指示ファイル（AGENTS.md）を生成します：

```bash
python adapters/codex/generate-instructions.py
```

生成された `AGENTS.md` を VS Code の Codex 設定ディレクトリに配置してください。

> **スキルのフォーマット**: Claude Code と Codex はいずれも
> [Agent Skills open standard](https://agentskills.io) の SKILL.md 形式を共有します。

---

## 開発者向け情報

### テストの実行

```bash
# 全テスト
python -m pytest

# ユニットテストのみ
python -m pytest tests/unit/

# 受入試験のみ
python -m pytest tests/acceptance/

# 特定のテストファイル
python -m pytest tests/acceptance/test_at10_lite.py -v
```

現在のテスト数：**264件**（ユニット + 受入試験）

### テスト一覧（受入試験）

| ファイル | 内容 |
|---------|------|
| `test_at02_first_half.py` | AT-02前半: アイディア生成・選定 |
| `test_at04.py` | AT-04: 出典管理・誠実性 |
| `test_at09.py` | AT-09: データ保護 |
| `test_at_phase6.py` | AT-02後半・AT-05・AT-06・AT-07: 原稿・レビュー |
| `test_at10_lite.py` | AT-10 Lite: Codex互換性・Visual Designer |

### CLI ツール一覧

| ツール | 説明 |
|--------|------|
| `scripts/deploy.py` | Claude Code へのスキルデプロイ |
| `scripts/project_cli.py` | 案件管理（create/status/list/advance-phase） |
| `scripts/idea_cli.py` | アイディア管理（create/add/select/reject） |
| `scripts/research_cli.py` | 調査・出典管理（create/add-source/mark-verified） |
| `scripts/planner_cli.py` | 企画書管理（create/save-plan/set-status） |
| `scripts/story_cli.py` | 構成表管理（create/add-section/reorder/set-status） |
| `scripts/writer_cli.py` | 原稿管理（save/start-revision/set-status） |
| `scripts/review_cli.py` | レビュー管理（create-review/add-finding/complete-review） |
| `scripts/visual_designer_cli.py` | レイアウト試作（generate/save-concept/status） |

### JSON スキーマ

```bash
python scripts/generate_schemas.py
```

`schemas/` ディレクトリに全モデルの JSON Schema が生成されます。

---

## ライセンス

このプロジェクトのライセンスは `LICENSE` ファイルを参照してください。
