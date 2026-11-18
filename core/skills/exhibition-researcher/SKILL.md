---
name: exhibition-researcher
description: 展示テーマに関する資料調査を行い、出典付き調査メモと出典台帳（source-registry.yaml）を作成する。「調査して」「資料を調べて」「出典を集めて」「researcher」「リサーチして」と依頼されたときに起動する。
---

# Exhibition Researcher

## 責務

展示テーマに関する資料調査を実施し、**出典台帳（source-registry.yaml）** と **調査メモ（research/memo-*.md）** を作成する。

## 出典誠実性ルール（絶対遵守・上書き不可）

1. **架空の出典・引用を作成しない**
2. **確認済み事実・研究上の解釈・AI推論を区別して記録する**
3. **出典不明の事実は `verification_status: unverified` として扱う**
4. **出典の確認状況を偽らない**

## 実行ルール

1. **調査結果は必ず出典付きで記録する**（出典不明な場合はその旨を明記）
2. **架空の書籍・論文・データを作成しない**
3. **出典台帳が存在しない場合は必ず作成してから調査メモを記録する**
4. **担当者の確認なしに「確認済み」にしない**

---

## STEP 0: 環境確認

### 0-1. deployment.yaml の読み込み

プロジェクトルートの `deployment.yaml` を Read ツールで読み込む。

- 見つからない場合 → 「`/exhibition-deployment-setup` を先に実行してください」と伝えて中断する

`data_root` を **DATA_ROOT** として記憶する。

### 0-2. project_id・museum_id の確認

担当者から確認する（会話で既出の場合はスキップ）：

> 「対象の案件IDと館IDを教えてください。」

**PROJECT_DIR** = `{DATA_ROOT}/{MUSEUM_ID}/{PROJECT_ID}`

---

## STEP 1: 出典台帳の確認・作成

```bash
python scripts/research_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

- `has_registry: false` の場合 → 新規作成：

```bash
python scripts/research_cli.py create \
  --project-dir "{PROJECT_DIR}" \
  --project-id "{PROJECT_ID}"
```

---

## STEP 2: 調査テーマの確認

担当者に確認する：

> 「どのようなテーマについて調査しますか？  
> また、調査の優先順位や参照したい資料があればお知らせください。」

調査テーマを **RESEARCH_THEME** として記憶する。

---

## STEP 3: 調査の実施

採用したアイディアのテーマ・ブリーフを踏まえ、以下の観点で調査内容を整理する：

| 調査観点 | 説明 |
|---------|------|
| 歴史的背景 | テーマに関わる時代・出来事の経緯 |
| 学術的知見 | 専門家・研究機関の見解・データ |
| 一次資料 | 館が所有または参照できる資料 |
| 未確認事項 | 確認が必要だが現時点では不明な点 |

**重要：** 以下を明確に区別する：

```
【確認済み事実】出典が確認できている情報
【研究上の解釈】専門家の解釈・学説（複数ある場合は併記）
【AI推論】AIが推測・補完した内容（出典なし）
【未確認】確認が必要だが調査できていない情報
```

---

## STEP 4: 出典の登録

調査で参照した出典を出典台帳に登録する。

```bash
python scripts/research_cli.py add-source \
  --project-dir "{PROJECT_DIR}" \
  --source-json '{"source_id":"src-001","type":"academic","title":"...","author":"...","year":2020,"verification_status":"unverified"}'
```

`verification_status` は原則 `"unverified"` として登録し、担当者が確認した後に `mark-verified` する。

---

## STEP 5: 調査メモの保存

調査内容をMarkdown形式でまとめて保存する。

```bash
python scripts/research_cli.py save-memo \
  --project-dir "{PROJECT_DIR}" \
  --memo-id "001" \
  --content "# 調査メモ 001：{RESEARCH_THEME}

## 確認済み事実

...

## 研究上の解釈

...

## AI推論（要確認）

...

## 未確認事項

- [ ] ...
"
```

---

## STEP 6: 未確認出典の確認

```bash
python scripts/research_cli.py get-unverified \
  --project-dir "{PROJECT_DIR}"
```

未確認出典がある場合は担当者に提示し、確認を促す：

> 「以下の出典について確認が必要です：  
> {unverified_list}  
>  
> 確認が取れたものについては `mark-verified` を実行してください。」

---

## STEP 7: 完了報告

> 「調査メモを作成しました。  
>  
> - 調査メモ：`{PROJECT_DIR}/research/memo-{MEMO_ID}.md`  
> - 出典台帳：`{PROJECT_DIR}/research/source-registry.yaml`  
> - 登録出典数：{total_sources}件  
> - 未確認：{unverified_count}件  
>  
> 未確認出典は担当者の確認後に `mark-verified` を実行してください。  
> 次のステップとして `/exhibition-planner` で企画書の作成に進めます。」

---

## 出典タイプ一覧

| タイプ | 説明 |
|--------|------|
| `primary_source` | 一次資料（文書・遺物・記録など） |
| `academic` | 学術論文・専門書 |
| `collection_item` | 館の所蔵資料 |
| `web` | ウェブサイト・データベース |
| `interview` | 専門家・関係者へのヒアリング |
| `other` | その他 |

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `出典IDが重複しています` | `src-00N` → `src-0{N+10}` 等に変更して再試行 |
| `出典が見つかりません` | `status` で登録済みIDを確認してから再試行 |
