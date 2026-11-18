---
name: exhibition-story-designer
description: 承認済み企画書を元に展示の章立て・ストーリー・構成表（story-structure-vN.yaml）を設計する。「構成を考えて」「章立てを作って」「ストーリーを設計して」「story designer」「展示の流れを決めて」と依頼されたときに起動する。
---

# Exhibition Story Designer

## 責務

承認済み企画書・調査メモ・館別プロファイルを元に **展示構成表（`story/story-structure-vN.yaml`）** を設計する。

## 実行ルール

1. **企画書が `approved` でない場合は構成設計を開始しない**
2. **来館者の動線・体験の流れを常に意識して設計する**
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

### 1-1. 企画書の確認

```bash
python scripts/planner_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

企画書が `approved` でない場合：

> 「企画書がまだ承認されていません。`/exhibition-planner` で企画書を承認してから構成設計に進んでください。」

→ 中断する。

### 1-2. 承認済み企画書の読み込み

Read ツールで `plan/exhibition-plan-v{N}.md` を読み込む。

### 1-3. 調査メモの確認（任意）

`research/` 内の調査メモがあれば Read ツールで読み込む。

### 1-4. 既存構成表の確認

```bash
python scripts/story_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

---

## STEP 2: 構成表の新規作成

### 2-1. 全体ストーリーラインのヒアリング

担当者に確認する：

> 「展示全体を通して来館者にどのような体験の流れを提供したいですか？  
> （例：「時系列で過去→現在→未来の順に体験する」「問いから始まり、発見・答えへと進む」など）」

### 2-2. 構成表の作成

```bash
python scripts/story_cli.py create \
  --project-dir "{PROJECT_DIR}" \
  --project-id "{PROJECT_ID}" \
  --version {N} \
  --overall-narrative "{OVERALL_NARRATIVE}"
```

---

## STEP 3: セクション設計

企画書のテーマと全体ストーリーラインを踏まえ、3〜7個のセクションを設計する。

各セクションには以下を含める：

| 項目 | 内容 |
|------|------|
| `section_id` | `sec-01`, `sec-02` ... |
| `title` | セクションタイトル（20字以内） |
| `narrative` | このセクションのストーリー説明（60字以内） |
| `key_messages` | 伝えたい主要メッセージ 1〜3個 |
| `exhibit_items` | 展示する主な資料・体験コンテンツ |
| `panel_count` | パネル枚数目安 |
| `display_order` | 展示順序 |

担当者にセクション案を提示してから保存する。

各セクションを保存：

```bash
python scripts/story_cli.py add-section \
  --project-dir "{PROJECT_DIR}" \
  --section-json '{"section_id":"sec-01","title":"...","narrative":"...","key_messages":[...],"exhibit_items":[...],"panel_count":3,"display_order":1}'
```

---

## STEP 4: 順序の調整

担当者から順序変更の要望があった場合：

```bash
python scripts/story_cli.py reorder \
  --project-dir "{PROJECT_DIR}" \
  --ordered-ids "sec-01,sec-03,sec-02,sec-04"
```

---

## STEP 5: 担当者レビューと承認

構成表を提示し、担当者に確認を求める：

> 「展示構成表 v{N} を作成しました。  
>  
> {セクション一覧をMarkdown形式で表示}  
>  
> 内容をご確認ください。  
> 承認する場合は「承認します」とお知らせください。  
> 変更がある場合は変更内容をお伝えください。」

承認の場合：

```bash
python scripts/story_cli.py set-status \
  --project-dir "{PROJECT_DIR}" \
  --story-status "approved"
```

---

## STEP 6: 完了報告

> 「展示構成表 v{N} が承認されました。  
>  
> - 構成表（YAML）：`{PROJECT_DIR}/story/story-structure-v{N}.yaml`  
> - 構成表（Markdown）：`{PROJECT_DIR}/story/story-structure-v{N}.md`  
>  
> 次のステップとして `/exhibition-writer` で各セクションの原稿を執筆できます。」

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `セクションIDが重複しています` | `sec-0N` → `sec-{N+10}` 等に変更して再試行 |
| `セクションが見つかりません` | `status` で登録済みIDを確認 |
