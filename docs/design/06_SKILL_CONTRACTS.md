# 06 Skills入出力契約

文書日：2026年11月18日  
文書区分：Phase 1 Skill契約設計  
ステータス：Phase 1確定（MVP契約。詳細はPhase別設計で確定）

---

## 1. 契約の形式と凡例

各Skillの契約は以下の形式で定義する。Phase 1では **責務・主要I/O・実行条件** を確定し、実装詳細はPhase別設計で確定する。

**実行環境：**  
現時点でサポートする実行環境は Claude Code のみ。  
Codex環境での各スキルの動作可否は、Phase 2初期のCodex Skills仕様調査（OI-02）の結果を受けて各契約に追記する。

| 項目 | 説明 |
|------|------|
| **責務** | Skillが果たすべき唯一の役割 |
| **入力** | Skillが必要とする主要な入力 |
| **出力** | Skillが生成・更新するもの |
| **依存設定** | 動作に必要なmuseum-profileの設定項目 |
| **実行条件** | Skillを実行できる前提状態 |
| **失敗時** | エラー・未実行時の動作 |
| **MVP優先度** | P0=MVP必須 / P1=初期製品化 / P2=将来拡張 |

---

## 2. Deployment Setup

**責務：** 実行環境を診断し、Skills・データ領域・設定ファイルを初期化する

| 項目 | 内容 |
|------|------|
| **入力** | ユーザーの環境情報（OS、パス、AI環境選定意思） |
| **出力** | `deployment.yaml`、`~/.claude/skills/`へのSkillインストール、動作検証レポート |
| **依存設定** | なし（初回セットアップ用） |
| **実行条件** | なし（最初に実行するSkill） |
| **失敗時** | 診断結果を提示し、手動手順を案内する |
| **MVP優先度** | P0 |

**主要な処理：**
1. OS・ツール・権限を確認する
2. `deployment.yaml` の作成をガイドする（`data_root`パスの設定）
3. `scripts/deploy.py` を実行してSkillsをインストールする
4. 読み取り・書き込み・承認の動作検証を実施する
5. 導入記録を `deployment.yaml` に追記する

---

## 3. Museum Onboarding

**責務：** 館の特性をヒアリングし、館別プロファイルを作成・承認する

| 項目 | 内容 |
|------|------|
| **入力** | ヒアリング回答、提供資料（任意）、`onboarding-session.yaml` |
| **出力** | `museum-profile-vN.yaml`、`profile-evidence-vN.yaml`、`onboarding-session.yaml`（更新） |
| **依存設定** | なし（プロファイル作成Skill） |
| **実行条件** | `deployment.yaml` が存在し、`data_root` が設定済み |
| **失敗時** | セッションを `paused` 状態で保存し、再開情報を提示する |
| **MVP優先度** | P0 |

詳細は `04_ONBOARDING_DESIGN.md` 参照。

---

## 4. Exhibition Director

**責務：** 展示制作の進行を統括し、各Skillへの作業指示・承認管理を行う

| 項目 | 内容 |
|------|------|
| **入力** | ユーザーの指示、`museum-profile`、`exhibition-project.yaml`、各Skillの出力 |
| **出力** | `exhibition-project.yaml`（状態更新）、`approval-record`、作業指示 |
| **依存設定** | `operations.approval_flow`、`operations.roles` |
| **実行条件** | 承認済み `museum-profile` が存在する |
| **失敗時** | 中断状態を `exhibition-project.yaml` に記録し、ユーザーに報告する |
| **MVP優先度** | P0 |

**権限境界：**  
- 承認済み原稿・企画書の変更は担当者承認なしに実行しない
- 外部送信・公開・印刷用最終確定は明示承認を必要とする

---

## 5. Idea Generator

**責務：** 展示テーマのアイディアを発散・比較・深掘りし、候補を整理する

| 項目 | 内容 |
|------|------|
| **入力** | ブリーフ（テーマ・対象者・期間等）、`museum-profile`、`idea-bank/`（過去候補） |
| **出力** | アイディア一覧（`ideas/idea-list.yaml`）、比較表（`ideas/comparison.md`） |
| **依存設定** | `basic.domains`、`exhibition_policy`、`visitors.target_groups` |
| **実行条件** | 承認済み `museum-profile` が存在する |
| **失敗時** | 生成できた候補を部分保存し、不足理由を報告する |
| **MVP優先度** | P0 |

---

## 6. Researcher

**責務：** 資料調査を実施し、出典付きの調査メモと出典台帳を作成する

| 項目 | 内容 |
|------|------|
| **入力** | 調査テーマ・範囲、`museum-profile`、`source-registry.yaml` |
| **出力** | 調査メモ（`research/memo-*.md`）、`source-registry.yaml`（更新）、未確認事項リスト |
| **依存設定** | `research.priority_sources`、`research.citation_style`、`research.unverified_handling` |
| **実行条件** | 調査テーマが確定している |
| **失敗時** | 確認済み情報のみを記録し、未確認・不明事項を明示する |
| **MVP優先度** | P0 |

**出典誠実性ルール（上書き不可）：**  
- 架空の出典・引用を作成しない
- 確認済み事実・研究上の解釈・AI推論を区別して記録する
- 出典不明の事実は「未確認」として扱う

---

## 7. Planner

**責務：** 企画書（目的・対象・コンセプト・実施条件）を作成・修正する

| 項目 | 内容 |
|------|------|
| **入力** | 採用アイディア、調査結果、`museum-profile`、`exhibition-project.yaml` |
| **出力** | 企画書（`plan/exhibition-plan-vN.md`）、`artifact-manifest.yaml`（更新） |
| **依存設定** | `exhibition_policy`、`visitors`、`operations.output_formats` |
| **実行条件** | テーマ候補が選定されている |
| **失敗時** | 作成済み部分を下書きとして保存し、未完成箇所を明示する |
| **MVP優先度** | P0 |

---

## 8. Story Designer

**責務：** 展示の章立て・ストーリー・展示資料の配置案を設計する

| 項目 | 内容 |
|------|------|
| **入力** | 承認済み企画書、調査結果、`museum-profile` |
| **出力** | 章立て・構成表（`story/story-structure-vN.yaml`）、展示資料配置案 |
| **依存設定** | `exhibition_policy`、`design.panel_specs`（参考） |
| **実行条件** | 企画書が `approved` 状態 |
| **失敗時** | 作成済み構成を下書きとして保存する |
| **MVP優先度** | P0 |

---

## 9. Exhibition Writer

**責務：** パネル・キャプション等の原稿を執筆・改訂する

| 項目 | 内容 |
|------|------|
| **入力** | 承認済み構成表、調査結果・出典、`museum-profile` |
| **出力** | 原稿ファイル群（`manuscripts/panel-*.md`等）、`artifact-manifest.yaml`（更新） |
| **依存設定** | `writing`（文体・文字数・用語集）、`research.citation_style` |
| **実行条件** | 展示構成が `approved` 状態 |
| **失敗時** | 作成済み原稿を下書きとして保存し、未作成箇所を一覧で示す |
| **MVP優先度** | P0 |

**改訂モード：**  
- 原本（既存原稿）は上書きしない
- 改訂版を別ファイルとして保存し、差分と変更理由を記録する

---

## 10. Visual Designer

**責務：** デザインコンセプト・レイアウト試作（HTML/CSS等の編集可能な形式）を作成する

| 項目 | 内容 |
|------|------|
| **入力** | 承認済み原稿、`museum-profile`、デザインガイド（任意） |
| **出力** | デザインコンセプト文書（`design/concept.md`）、レイアウト試作（HTML等） |
| **依存設定** | `design.design_guide_path`、`design.panel_specs` |
| **実行条件** | 主要原稿が `approved` 状態 |
| **失敗時** | 完成したパーツのみ出力し、未完成を明示する |
| **MVP優先度** | P1 |

---

## 11. Advocate

**責務：** 展示内容・制作物に対して批判的検討を行い、論点・見落とし・代替案を提示する

| 項目 | 内容 |
|------|------|
| **入力** | 対象成果物、`museum-profile`、`source-registry.yaml` |
| **出力** | `review-record.yaml`（`reviewer_role: advocate`） |
| **依存設定** | `quality.advocate_criteria` |
| **実行条件** | 対象成果物が `ready_for_review` 状態 |
| **失敗時** | 検討できた範囲を記録し、未確認箇所を明示する |
| **MVP優先度** | P0 |

**Advocateの評価観点（標準）：**
- そもそもこの企画・構成でよいか（方向性の妥当性）
- 来館者視点からの問題点
- 見落とされている重要な論点・テーマ
- 根拠・出典の妥当性への疑問
- 代替案・改善の可能性

指摘の採否は担当者が決定する。Advocate自身が修正を加えない。

---

## 12. Reviewer

**責務：** 成果物が要件・基準を満たしているかを検証し、問題点を指摘する

| 項目 | 内容 |
|------|------|
| **入力** | 対象成果物、`museum-profile`、`source-registry.yaml` |
| **出力** | `review-record.yaml`（`reviewer_role: reviewer`） |
| **依存設定** | `quality.reviewer_criteria`、`writing`、`research.citation_style` |
| **実行条件** | 対象成果物が `ready_for_review` 状態 |
| **失敗時** | 検証できた範囲を記録し、未確認箇所を明示する |
| **MVP優先度** | P0 |

**Reviewerの評価観点（標準）：**
- 事実の正確性・出典の存在確認
- 表記・用語の統一（writing規程との照合）
- 文字数・形式要件の適合
- 権利・利用許諾の確認状況
- プロファイル要件への適合

指摘の採否は担当者が決定する。Reviewer自身が修正を加えない。

---

## 13. Skills間の連携フロー（MVP）

```
Deployment Setup
    ↓
Museum Onboarding → 館別プロファイル（承認済み）
    ↓
Exhibition Director ─┬→ Idea Generator → アイディア選定（承認）
                     ├→ Researcher → 出典台帳（確認）
                     ├→ Planner → 企画書（承認）
                     ├→ Story Designer → 構成表（承認）
                     ├→ Exhibition Writer → 原稿（承認）
                     │      ↑ Advocate（重要承認ポイント前に介入）
                     │      ↑ Reviewer（重要承認ポイント前に介入）
                     └→ Visual Designer → レイアウト試作（P1）
```

**AdvocateとReviewerの介入タイミング（標準）：**
- 企画書の承認前
- 展示構成の承認前
- 主要原稿の承認前
