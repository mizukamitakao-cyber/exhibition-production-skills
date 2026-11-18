# 03 共通データモデル設計

文書日：2026年11月18日  
文書区分：Phase 1 データモデル設計  
ステータス：Phase 1確定

---

## 1. データモデル一覧と関係

### 1.1 設定の4階層とデータモデルの対応

| 階層 | 設定ファイル | 保存場所 |
|------|-----------|---------|
| ① 共通設定 | `core/policies/common-settings.yaml` | 製品リポジトリ |
| ② 専門分野別設定 | `core/knowledge/domains/{domain}/domain-settings.yaml` | 製品リポジトリ |
| ③ 館別設定 | `museum-profile-v{N}.yaml` | 館別データ領域 |
| ④ 案件別設定 | `exhibition-project.yaml` の `brief.*` | 館別データ領域 |

①②は製品リポジトリで管理し、本節のデータモデルは③④を中心に定義する。  
設定の解決順序は `02_ARCHITECTURE_DESIGN.md` §4を参照。

### 1.2 データモデルの関係

```
[共通設定①] ─→ [専門分野別設定②]
                        │
museum-profile③ ─────── profile-evidence（設定根拠）
     │   └── onboarding-session（作成元）
     │
     └── exhibition-project④
              │
              ├── artifact-manifest（成果物管理・ハッシュ台帳）
              ├── source-registry（出典管理）
              ├── review-record（レビュー記録）
              ├── approval-record（承認記録）
              └── operation-record（操作記録）
```

---

## 2. ID・ファイル名規則

| 種別 | 形式 | 例 |
|------|------|-----|
| museum-id | スラッグ（英小文字・ハイフン） | `natural-history-museum-001` |
| project-id | `{year}-{slug}-{3桁連番}` | `2026-dinosaur-exhibition-001` |
| session-id | `onboarding-{museum-id}-{YYYYMMDD}` | `onboarding-nhm-001-20261118` |
| artifact-id | `{project-id}-{type}-v{版番号}` | `2026-dinosaur-001-plan-v2` |
| review-id | `review-{artifact-id}-{YYYYMMDDHHMMSS}` | `review-...-20261118143000` |
| approval-id | `approval-{artifact-id}-{YYYYMMDDHHMMSS}` | — |
| operation-id | 自動採番（UUIDまたは連番） | — |

---

## 3. スキーマ版管理

すべてのデータモデルに `schema_version` フィールドを持つ。

```yaml
schema_version: "1.0"   # メジャー.マイナー形式
```

- **マイナー更新**（後方互換）：フィールド追加、任意フィールド変更
- **メジャー更新**（破壊的変更）：必須フィールド変更、構造変更
- メジャー更新時はマイグレーションスクリプトを `scripts/migrate/` に配置する

---

## 4. 各モデルの定義

### 4.1 museum-profile

**目的：** 館の特性・方針・規程を集約した館別設定

**保存先：** `{data_root}/museums/{museum-id}/profile/museum-profile-v{N}.yaml`

```yaml
schema_version: "1.0"
museum_id: "natural-history-museum-001"
profile_version: 1               # 整数（更新のたびにインクリメント）
status: "draft"                  # draft | ready_for_review | approved | revision_in_progress
created_at: ""                   # ISO 8601 (Asia/Tokyo)
updated_at: ""
approved_at: null
approved_by: null                # 承認者の識別情報（任意形式）

basic:
  name: ""                       # 館の正式名称
  type: ""                       # museum | archive | cultural_facility | other
  purpose: ""                    # 設置目的・使命
  domains: []                    # history | art | natural_history | science | other （複数可）

visitors:
  target_groups: []              # 例: ["一般市民", "小中学生", "研究者"]
  languages: []                  # 例: ["ja", "en"]
  accessibility_requirements: [] # 例: ["大活字対応", "音声ガイド対応"]

exhibition_policy:
  purpose: ""                    # 展示の主な目的
  education_policy: ""           # 教育方針
  key_themes: []                 # 重点テーマ
  content_restrictions: []       # 避けるべき表現・内容

research:
  priority_sources: []           # 例: ["一次資料優先", "学術論文", "収蔵品DB"]
  citation_style: ""             # 例: "注釈形式（脚注）"
  unverified_handling: ""        # 未確認情報の取り扱い方針
  ai_content_policy: ""          # AI生成内容の取り扱い方針

writing:
  style: ""                      # 文体（例: "である体"）
  honorific_level: ""            # 敬語レベル（例: "丁寧語なし"）
  max_chars_panel: null          # パネルの最大文字数（整数）
  max_chars_caption: null        # キャプションの最大文字数
  vocabulary: {}                 # 統一用語集 {標準形: [表記ゆれリスト]}
  notation_rules: []             # 表記統一ルール

design:
  design_guide_path: null        # デザインガイドへの相対パス（任意）
  panel_specs: {}                # パネル仕様 {size: "B1", orientation: "portrait"}

quality:
  advocate_criteria: []          # Advocateが確認する観点
  reviewer_criteria: []          # Reviewerが確認する観点

operations:
  approval_flow: []              # 承認段階のリスト
  roles: {}                      # 役割定義 {担当者識別: 役割名}
  output_formats: []             # 成果物形式 例: ["Word", "PDF"]

data_management:
  ai_input_restrictions: []      # AIへの入力制限事項
  storage_path: ""               # この館のデータルートパス（絶対または相対）
  backup_policy: ""              # バックアップ方針（記述）
```

**ステータス遷移：** `draft` → `ready_for_review` → `approved` / `revision_in_progress`

---

### 4.2 profile-evidence

**目的：** プロファイル各設定値の根拠・確認状態を管理する

**保存先：** `{museum-id}/profile/profile-evidence-v{N}.yaml`

```yaml
schema_version: "1.0"
museum_id: ""
profile_version: 1               # 対応するmuseum-profileのversion
updated_at: ""

# フィールドパスをキーとし、根拠情報を記録
evidence:
  "basic.name":
    status: "confirmed"          # confirmed | documented | proposed | unset | conflict
    source: "公式ウェブサイト"
    confirmed_at: ""
    note: ""
  "writing.max_chars_panel":
    status: "proposed"
    source: "ヒアリング回答"
    confirmed_at: ""
    note: "担当者の経験則。公式規程文書での確認推奨"
  "exhibition_policy.content_restrictions":
    status: "unset"
    source: null
    confirmed_at: null
    note: "未回答。次回セッションで確認"
```

**status の意味：**

| 値 | 意味 |
|----|------|
| `confirmed` | 公式文書または担当者確認済み |
| `documented` | 提供資料に記載あり（担当者確認未実施） |
| `proposed` | AIまたはヒアリングによる提案（未確認） |
| `unset` | 未設定・未回答 |
| `conflict` | 資料間で矛盾あり（要確認） |

---

### 4.3 onboarding-session

**目的：** Museum Onboardingのヒアリング進捗・状態を管理する

**保存先：** `{museum-id}/profile/onboarding-session.yaml`（1館につき1セッションファイル）

```yaml
schema_version: "1.0"
session_id: ""
museum_id: ""
status: "not_started"            # not_started | in_progress | paused | ready_for_review | approved | revision_in_progress
created_at: ""
updated_at: ""
paused_at: null
paused_reason: ""

current_phase: ""                # basic | visitors | exhibition_policy | research | writing | design | quality | operations
completed_phases: []             # 完了フェーズのリスト

answered_questions: []           # {question_id, answer, answered_at, source}
pending_questions: []            # {question_id, phase, priority}
skipped_questions: []            # {question_id, reason}

provided_documents: []           # {filename, extracted_at, fields_updated}
conflicts: []                    # {field_path, value_a, source_a, value_b, source_b, detected_at}

profile_draft_version: null      # 生成中のプロファイル版番号
notes: ""                        # 自由記述メモ
```

---

### 4.4 exhibition-project

**目的：** 展示案件の基本情報・状態を管理する

**保存先：** `{museum-id}/projects/{project-id}/project.yaml`

```yaml
schema_version: "1.0"
project_id: ""
museum_id: ""
profile_version: 1               # 使用したmuseum-profileの版（固定）
title: ""
type: "new"                      # new | revision
status: "planning"               # planning | in_progress | review | approved | completed | suspended
created_at: ""
updated_at: ""

revision_source: null            # typeがrevisionの場合、元案件ID

brief:
  theme: ""
  target_visitors: []
  period: ""                     # 開催期間（記述形式）
  venue: ""
  constraints: []                # 制約条件

current_phase: ""                # idea | research | planning | story | manuscript | design | review | final
completed_phases: []

director_notes: ""               # Exhibition Directorのメモ
```

---

### 4.5 artifact-manifest

**目的：** 案件内の成果物の版と状態を管理する

**保存先：** `{project-id}/artifact-manifest.yaml`

```yaml
schema_version: "1.0"
project_id: ""
updated_at: ""

artifacts:
  - artifact_id: ""
    type: ""                     # idea-list | research-memo | plan | story-structure | manuscript | design-concept | review
    title: ""
    version: 1
    revision: 1                  # 改訂回数（楽観的競合検出用。更新のたびにインクリメント）
    status: "draft"              # draft | ready_for_review | approved | superseded
    file_path: ""                # プロジェクトフォルダからの相対パス
    sha256: ""                   # 承認時に計算したSHA-256ハッシュ（整合性検証用）
    created_at: ""
    updated_at: ""
    approved_at: null
    approved_by: null
    parent_artifact_id: null     # 改訂元の成果物ID
    review_ids: []               # この成果物に対するreview-recordのIDリスト
    approval_ids: []
```

---

### 4.6 source-registry

**目的：** 調査資料・出典を管理し、事実の根拠を追跡可能にする

**保存先：** `{project-id}/research/source-registry.yaml`

```yaml
schema_version: "1.0"
project_id: ""
updated_at: ""

sources:
  - source_id: ""               # 例: src-001
    type: ""                    # primary_source | academic | collection_item | web | interview | other
    title: ""
    author: ""
    year: null
    location: ""                # 所蔵先・URL等
    pages: ""                   # 参照箇所
    retrieved_at: null          # Web資料の場合の参照日
    verification_status: ""     # verified | unverified | disputed
    access_permission: ""       # permission_obtained | public_domain | unknown | restricted
    local_path: null            # ローカルコピーのパス（任意）
    notes: ""

# 出典と成果物の対応（MVP：source_id → 使用箇所の対応を保持する）
# 注：複雑な事実追跡（claim・certainty）はMVPスコープ外。Phase 6以降で検討。
source_usage:
  - source_id: ""               # 参照する出典のID（上記 sources リストの source_id）
    used_in_artifacts: []       # この出典を参照している成果物IDリスト
    sections: ""                # 成果物内の参照箇所の説明（任意）
```

---

### 4.7 review-record

**目的：** AdvocateとReviewerの指摘を記録する

**保存先：** `{project-id}/reviews/review-{artifact-id}-{timestamp}.yaml`

```yaml
schema_version: "1.0"
review_id: ""
artifact_id: ""
reviewer_role: ""               # advocate | reviewer
reviewed_at: ""

findings:
  - finding_id: ""
    type: ""                    # logical_issue | factual_issue | expression_issue | requirement_gap | suggestion
    severity: ""                # critical | major | minor | info
    location: ""                # 対象箇所の説明
    description: ""             # 指摘内容
    recommendation: ""          # 改善提案（任意）
    status: "pending"           # pending | accepted | rejected | deferred
    resolved_at: null
    resolution_note: ""

overall_assessment: ""          # 総合評価コメント
proceed_recommendation: null    # true | false | null（条件付き）
```

---

### 4.8 approval-record

**目的：** 承認・差し戻しの記録を管理する

**保存先：** `{project-id}/reviews/approval-{artifact-id}-{timestamp}.yaml`

```yaml
schema_version: "1.0"
approval_id: ""
artifact_id: ""
artifact_version: null
decision: ""                    # approved | rejected | conditional_approval
decided_at: ""
decided_by: ""                  # 承認者の識別情報

conditions: []                  # conditional_approvalの場合の条件
rejection_reason: ""            # rejectedの場合の理由
notes: ""

review_record_ids: []           # 参照したreview-recordのIDリスト
previous_approval_id: null      # 再承認の場合、前回の承認ID
```

---

### 4.9 operation-record

**目的：** 保存・変更・削除等の操作を監査記録として残す

**保存先：** `{museum-id}/system/operation-log.yaml`（追記型）

```yaml
schema_version: "1.0"
museum_id: ""

operations:
  - operation_id: ""            # UUIDまたは連番
    timestamp: ""               # ISO 8601 (Asia/Tokyo)
    operation: ""               # write | read | delete | approve | reject | backup | restore
    target_path: ""             # 操作対象ファイルのパス
    actor: ""                   # 実行スキル名
    session_context: ""         # 実行時のセッション識別（任意）
    success: true
    error: null                 # エラーメッセージ（失敗時）
    details: {}                 # 操作種別ごとの追加情報
```

---

## 5. YAML / JSON Schema / Pydantic 利用方針

### 5.1 ライブラリの役割分担

| ライブラリ | 役割 | 理由 |
|-----------|------|------|
| `ruamel.yaml` | YAMLのパース・シリアライズ | コメントとフォーマットを保持するラウンドトリップ対応 |
| `pydantic v2` | データモデル定義・型検証・制約チェック | 実行時バリデーションの主体。型安全で活発なコミュニティ |
| JSON Schema | Pydanticモデルから**自動生成** | ツール連携・ドキュメント用途。手動管理しない |

**JSON Schemaの生成方法：**  
`scripts/generate_schemas.py` がPydanticモデルから一括生成する。`schemas/*.schema.json` は生成物であり手動編集しない。

```python
# 生成例
from pydantic import BaseModel
# schema.json = MuseumProfile.model_json_schema()
```

### 5.2 検証のタイミング

| タイミング | 検証内容 |
|---------|---------|
| 書き込み前 | Pydanticモデルでスキーマ検証（失敗時は書き込み中止） |
| 承認済みファイルの読み込み前 | SHA-256ハッシュによる整合性検証 |
| セッション開始時 | museum-profileのスキーマ整合性を確認 |
| マイグレーション時 | 旧スキーマ→新スキーマへの自動変換 |

### 5.3 追加ライブラリ（Phase 2実装前に確定）

- `pydantic v2`：採用確定
- `ruamel.yaml`：採用確定
- JSON Schema自動生成：`model_json_schema()` 使用（追加ライブラリ不要）
