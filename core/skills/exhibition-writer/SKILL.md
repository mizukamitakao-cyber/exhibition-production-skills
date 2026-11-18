---
name: exhibition-writer
description: 承認済み展示構成表を元にパネル・キャプション等の原稿を執筆・改訂する。「原稿を書いて」「パネルを執筆して」「キャプションを作成して」「writer」「原稿の改訂をして」と依頼されたときに起動する。
---

# Exhibition Writer

## 責務

承認済み展示構成表・調査メモ・出典台帳・館別プロファイルを元に **原稿（`manuscripts/{panel_id}-v{N}.md`）** を執筆する。

## 実行ルール（必ず守る）

1. **展示構成表が `approved` でない場合は原稿作成を開始しない**
2. **原本（既存原稿）を上書きしない。改訂版は必ず新しいバージョンとして保存する**
3. **出典のある記述は `source_id` を参照する。出典のない重要事実は明示する**
4. **担当者の承認なしに `approved` にしない**
5. **文字数制限（館プロファイルの `writing.panel_max_chars` 等）を守る**

---

## STEP 0: 環境確認

### 0-1. deployment.yaml の読み込み

プロジェクトルートの `deployment.yaml` を Read ツールで読み込む。

- 見つからない場合 → 「`/exhibition-deployment-setup` を先に実行してください」と伝えて中断する

`data_root` を **DATA_ROOT** として記憶する。

### 0-2. project_id・museum_id の確認

**PROJECT_DIR** = `{DATA_ROOT}/{MUSEUM_ID}/{PROJECT_ID}`

---

## STEP 1: 前提確認

### 1-1. 展示構成表の確認

```bash
python scripts/story_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

`status` が `approved` でない場合：

> 「展示構成表がまだ承認されていません。`/exhibition-story-designer` で承認してから原稿作成に進んでください。」

→ 中断する。

### 1-2. 承認済み構成表の読み込み

Read ツールで `story/story-structure-v{N}.md` を読み込む。

### 1-3. 調査メモ・出典台帳の確認（任意）

```bash
python scripts/research_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

### 1-4. 既存原稿の確認

```bash
python scripts/writer_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

---

## STEP 2: 原稿対象の確認

担当者に確認する：

> 「どのパネルの原稿を作成しますか？  
> （例：`panel-01`〜`panel-{N}`、`caption-01`など）  
> 全セクション分作成する場合はその旨お知らせください。」

対象を **PANEL_IDS** として記憶する。

---

## STEP 3: 原稿執筆

各パネルについて以下の形式で原稿を作成する：

```markdown
# {パネルタイトル}

**セクション**：{section_title}  
**パネルID**：{panel_id}  
**文字数目安**：{target_chars}字以内  
**出典**：{source_ids}

---

{本文（担当者の承認なしに事実を推測で補わない。不明点は「（要確認）」と明記する）}
```

---

## STEP 4: 原稿の保存

```bash
python scripts/writer_cli.py save \
  --project-dir "{PROJECT_DIR}" \
  --panel-id "{PANEL_ID}" \
  --content "{CONTENT}" \
  --title "{TITLE}"
```

---

## STEP 5: 担当者レビューと承認

原稿を提示し、担当者に確認を求める。

承認の場合：

```bash
python scripts/writer_cli.py set-status \
  --project-dir "{PROJECT_DIR}" \
  --artifact-id "{PANEL_ID}-v{N}" \
  --artifact-status "approved"
```

---

## STEP 6（改訂モード）: 既存原稿の改訂

改訂が必要な場合（「この原稿を修正して」「改訂版を作って」）：

### 6-1. 改訂版の準備

```bash
python scripts/writer_cli.py start-revision \
  --project-dir "{PROJECT_DIR}" \
  --panel-id "{PANEL_ID}"
```

原本は **保持される**。新バージョン番号が返される。

### 6-2. 改訂版の執筆・保存

新しいバージョン番号で原稿を保存する（STEP 3〜4と同じ）。

---

## 注意事項

- Advocate・Reviewer の指摘が `accepted` の場合は反映した改訂版を作成する
- 指摘が `rejected` の場合は元の原稿は変更しない
- 1回の作業で執筆するパネル数は担当者と合意する（全量を一度に作成しない）

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `story-structure が見つかりません` | Story Designer スキルで構成表を作成・承認してから再試行 |
| `原稿が存在しません` | `save` サブコマンドで新規作成 |
