---
name: exhibition-planner
description: 採用されたアイディアと調査結果を元に企画書（exhibition-plan-vN.md）を作成する。「企画書を作って」「展示計画をまとめて」「planner」「プランを立てて」と依頼されたときに起動する。
---

# Exhibition Planner

## 責務

採用アイディア・調査メモ・館別プロファイルを元に **企画書（`plan/exhibition-plan-vN.md`）** を作成し、artifact-manifest.yaml に登録する。

## 実行ルール

1. **採用アイディアが選定されていない場合は企画書を作成しない**
2. **出典のある記述は必ず source_id を参照する**
3. **担当者の承認なしに `approved` にしない**
4. **改訂版は新しいバージョン番号で保存する（上書き禁止）**

---

## STEP 0: 環境確認

### 0-1. deployment.yaml の読み込み

プロジェクトルートの `deployment.yaml` を Read ツールで読み込む。

- 見つからない場合 → 「`/exhibition-deployment-setup` を先に実行してください」と伝えて中断する

`data_root` を **DATA_ROOT** として記憶する。

### 0-2. project_id・museum_id の確認

担当者から確認する（会話で既出の場合はスキップ）。

**PROJECT_DIR** = `{DATA_ROOT}/{MUSEUM_ID}/{PROJECT_ID}`

---

## STEP 1: 前提確認

### 1-1. プロジェクト状態の確認

```bash
python scripts/project_cli.py status \
  --project-path "{PROJECT_DIR}/exhibition-project.yaml"
```

### 1-2. アイディア選定の確認

```bash
python scripts/idea_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

`selected_idea_id` が `null` の場合：

> 「採用されたアイディアがありません。`/exhibition-idea-generator` でアイディアを選定してから企画書を作成してください。」

→ 中断する。

### 1-3. 調査メモの確認（任意）

`{PROJECT_DIR}/research/` ディレクトリ内の調査メモがあれば Read ツールで読み込む。

### 1-4. 既存企画書の確認

```bash
python scripts/planner_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

---

## STEP 2: マニフェストの作成（初回のみ）

`has_manifest: false` の場合：

```bash
python scripts/planner_cli.py create \
  --project-dir "{PROJECT_DIR}" \
  --project-id "{PROJECT_ID}"
```

---

## STEP 3: 企画書の執筆

以下の構成で企画書を作成する：

```markdown
# 企画書 — {タイトル}

**案件ID**：{project_id}  
**作成日**：{YYYY-MM-DD}  
**バージョン**：v{N}

---

## 1. 展示の目的

{この展示で何を達成したいか。来館者にどのような経験・知識を提供するか。}

## 2. 対象来館者

{主な対象層。年齢・関心・知識水準など。}

## 3. 展示コンセプト

{採用アイディアのコンセプトを展開する。}

## 4. 主要テーマと内容

{テーマごとに展示する内容を記述する。}

## 5. 会場・期間・規模

- 会場：{venue}
- 期間：{period}
- 規模目安：{estimated_scale}

## 6. 制約・特記事項

{予算・資料利用制限・技術的制約など。}

## 7. 参照出典

{使用した出典の一覧（source_id と書名/URL）。}
```

---

## STEP 4: 企画書の保存

```bash
python scripts/planner_cli.py save-plan \
  --project-dir "{PROJECT_DIR}" \
  --content "{PLAN_CONTENT}" \
  --version {N} \
  --title "{PLAN_TITLE}"
```

---

## STEP 5: 担当者レビューと承認

企画書を提示し、担当者に確認を求める：

> 「企画書 v{N} を作成しました（`plan/exhibition-plan-v{N}.md`）。  
>  
> 内容をご確認ください。  
> 修正の必要がなければ「承認します」とお知らせください。  
> 修正がある場合は修正点をお伝えください。」

承認の場合：

```bash
python scripts/planner_cli.py set-status \
  --project-dir "{PROJECT_DIR}" \
  --artifact-id "plan-v{N}" \
  --artifact-status "approved"
```

修正がある場合 → v{N+1} として保存（STEP 3に戻る）。

---

## STEP 6: 完了報告

> 「企画書 v{N} が承認されました。  
>  
> - 企画書：`{PROJECT_DIR}/plan/exhibition-plan-v{N}.md`  
>  
> 次のステップとして `/exhibition-story-designer` で展示の章立て・構成表を設計できます。」

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `成果物IDが重複しています` | バージョン番号を確認して再試行 |
| `成果物が見つかりません` | `status` で登録済みIDを確認 |
