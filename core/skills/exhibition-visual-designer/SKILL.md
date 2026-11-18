---
name: exhibition-visual-designer
description: 承認済み原稿を元にパネルのHTML/CSSレイアウト試作を生成する。「デザインして」「レイアウトを作って」「パネルのHTML試作」「visual designer」と依頼されたときに起動する。
---

# Exhibition Visual Designer

## 責務

承認済み原稿・館別プロファイルのデザイン設定を元に **HTML/CSSパネルレイアウト試作（`design/panel-{panel_id}.html`）** を生成する。

## 実行ルール（必ず守る）

1. **承認済み原稿（`approved`）が存在しない場合はレイアウト生成を開始しない**
2. **生成した HTML は「試作」である。印刷・展示への直接使用前に担当者が確認する**
3. **テキスト内容を変更しない。原稿の文章はそのまま HTML に変換する**
4. **館プロファイルの `design.panel_specs` があれば優先して適用する**

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

### 1-1. 原稿の確認

```bash
python scripts/writer_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

承認済み原稿（`artifact_status: approved`）が0件の場合：

> 「承認済みの原稿がありません。`/exhibition-writer` で原稿を作成・承認してから再試行してください。」

→ 中断する。

### 1-2. 既存レイアウトの確認

```bash
python scripts/visual_designer_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

---

## STEP 2: デザイン方針の確認

担当者に確認する：

> 「どのパネルのレイアウト試作を生成しますか？  
> （例：`panel-01`、全パネル など）  
>
> また、以下のデザイン設定をカスタマイズしますか？（省略可）  
> - 背景色（デフォルト: 白 `#ffffff`）  
> - アクセントカラー（デフォルト: 青 `#2c5f8a`）  
> - パネル幅（デフォルト: `800px`）  
>
> 館プロファイルに `design.panel_specs` が設定されている場合は自動で適用されます。」

対象を **PANEL_IDS** として記憶する。  
カスタム設定があれば **CUSTOM_SPECS** として記憶する。

---

## STEP 3: 原稿の読み込み

各パネルについて、承認済み最新原稿を Read ツールで読み込む：

```
{PROJECT_DIR}/manuscripts/{panel_id}-v{N}.md
```

`N` は承認済みの最新バージョン番号。

---

## STEP 4: HTML レイアウトの生成

各パネルについて生成コマンドを実行する：

```bash
python scripts/visual_designer_cli.py generate \
  --project-dir "{PROJECT_DIR}" \
  --panel-id "{PANEL_ID}" \
  --title "{PANEL_TITLE}" \
  --content "{CONTENT}" \
  --footer "{MUSEUM_NAME} · {PROJECT_NAME}" \
  [--bg-color "{BG_COLOR}"] \
  [--accent-color "{ACCENT_COLOR}"] \
  [--panel-width "{PANEL_WIDTH}"]
```

`CONTENT` が長い場合は `--content-file` オプションを使用して一時ファイル経由で渡す：

```bash
# 一時ファイルに書き出してから渡す
python scripts/visual_designer_cli.py generate \
  --project-dir "{PROJECT_DIR}" \
  --panel-id "{PANEL_ID}" \
  --title "{PANEL_TITLE}" \
  --content-file "{TEMP_FILE_PATH}" \
  --footer "{MUSEUM_NAME} · {PROJECT_NAME}"
```

---

## STEP 5: 結果確認と担当者への提示

```bash
python scripts/visual_designer_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

担当者に結果を報告する：

> 「以下のパネルのHTMLレイアウト試作を生成しました：
>
> {パネル一覧（panel_id: ファイルパス）}
>
> `design/panel-{panel_id}.html` をブラウザで開いて確認してください。
> 
> 修正が必要な場合は、次のいずれかの方法で対応できます：
> - カラーや幅の調整 → このスキルを再実行してください
> - 本文の内容修正 → `/exhibition-writer` で原稿を改訂してください」

---

## STEP 6（オプション）: デザインコンセプト文書の保存

デザインの意図・選択した色・フォント方針等をメモとして保存する場合：

```bash
python scripts/visual_designer_cli.py save-concept \
  --project-dir "{PROJECT_DIR}" \
  --content "{CONCEPT_TEXT}"
```

---

## 生成されるファイル構造

```
{PROJECT_DIR}/
  design/
    panel-{panel_id}.html   ← HTML/CSS試作（ブラウザで確認可能）
    concept.md              ← デザインコンセプトメモ（任意）
```

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `承認済み原稿がありません` | Writer スキルで原稿を作成・承認 |
| `deployment.yaml が見つかりません` | Deployment Setup スキルを先に実行 |
| `content-file が見つかりません` | 一時ファイルパスを確認する |
