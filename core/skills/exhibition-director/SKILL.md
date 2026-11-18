---
name: exhibition-director
description: 展示プロジェクト（企画案件）を新規作成し、状態管理・進捗確認を行う。「新しい展示を企画したい」「案件を作成して」「プロジェクトを始めたい」「exhibition director」「展示案件の確認」と依頼されたときに起動する。
---

# Exhibition Director

## 責務

担当者との対話を通じて **展示プロジェクト（exhibition-project.yaml）** を作成・管理する。  
案件の骨格（テーマ・期間・会場・対象来館者）を定め、次のスキルへ引き継ぐ。

## 実行ルール（必ず守る）

1. **承認済みプロファイルがない館では案件を作成しない**（要事前オンボーディング）
2. **担当者の確認なしにプロジェクト情報を確定しない**
3. **毎ステップの完了後に exhibition-project.yaml を保存する**（project_cli.py 経由）
4. **1回の返答で聞く事項は最大3項目**

---

## STEP 0: 環境確認

### 0-1. deployment.yaml の読み込み

プロジェクトルートの `deployment.yaml` を Read ツールで読み込む。

- 見つからない場合 → 「`/exhibition-deployment-setup` を先に実行してください」と伝えて中断する

`data_root` の値を **DATA_ROOT** として記憶する。

### 0-2. 操作種別の判定

担当者の発言から以下を判定する：

| 発言例 | 操作 |
|--------|------|
| 「新しい展示を企画したい」「案件を作成して」 | 新規作成（STEP 1へ） |
| 「案件の状況を確認して」「進捗を見せて」 | 状態確認（STEP 5へ） |

---

## STEP 1: museum_id の確定

担当者に確認する：

> 「どの館の案件を作成しますか？  
> 館の識別子（museum_id）を教えてください（例：`museum-001`）。」

確定した museum_id を **MUSEUM_ID** として記憶する。  
**MUSEUM_DIR** = `{DATA_ROOT}/{MUSEUM_ID}`

---

## STEP 2: 前提条件の確認

Bash ツールで実行：

```bash
python scripts/project_cli.py check-prerequisites \
  --museum-dir "{MUSEUM_DIR}"
```

結果の `has_approved_profile` が `false` の場合：

> 「この館にはまだ承認済みプロファイルがありません。  
> `/exhibition-museum-onboarding` でオンボーディングを完了してから、再度お試しください。」

→ 中断する。

---

## STEP 3: project_id の確定

担当者に確認する：

> 「案件の識別子（project_id）を設定します。  
> 推奨形式：`project-20260401`（開催予定年月）や `tokuten-2026`（企画名略称）など。  
> 希望の識別子を教えてください。」

確定した project_id を **PROJECT_ID** として記憶する。  
**PROJECT_DIR** = `{MUSEUM_DIR}/{PROJECT_ID}`  
**PROJECT_PATH** = `{PROJECT_DIR}/exhibition-project.yaml`

---

## STEP 4: 案件骨格のヒアリング（最大3項目ずつ）

以下の項目を対話で確認する。3項目ごとに保存する。

### 第1ターン
1. **展示タイトル（仮）**：例「縄文時代の食と暮らし」
2. **展示テーマ**：伝えたい核心メッセージ
3. **開催予定期間**：例「2027年4月〜7月」

Bash ツールで進捗保存（title 確定後）：

```bash
python scripts/project_cli.py create \
  --project-id "{PROJECT_ID}" \
  --museum-id "{MUSEUM_ID}" \
  --museum-dir "{MUSEUM_DIR}" \
  --title "{TITLE}"
```

### 第2ターン
4. **会場**：例「第2展示室（200㎡）」
5. **対象来館者**：例「小学生、家族連れ」
6. **制約・条件**：予算上限・貸出不可資料・設備制約など

Bash ツールでブリーフ更新：

```bash
python scripts/project_cli.py update-brief \
  --project-path "{PROJECT_PATH}" \
  --theme "{THEME}" \
  --period "{PERIOD}" \
  --venue "{VENUE}" \
  --target-visitors "{TARGET_VISITORS}" \
  --constraints "{CONSTRAINTS}"
```

---

## STEP 5: 状態確認

Bash ツールで実行：

```bash
python scripts/project_cli.py status \
  --project-path "{PROJECT_PATH}"
```

結果を整形して担当者に提示する：

```
【案件状況】
案件ID     : {project_id}
タイトル   : {title}
ステータス : {status}
現在フェーズ: {current_phase}
完了フェーズ: {completed_phases}
テーマ     : {brief.theme}
期間       : {brief.period}
対象来館者 : {brief.target_visitors}
```

---

## STEP 6: 次のステップ案内

案件作成が完了したら担当者に伝える：

> 「案件「{TITLE}」（`{PROJECT_ID}`）を作成しました。  
>  
> 次のステップとして、以下を提案します：  
> - **アイディア生成**：`/exhibition-idea-generator` でコンセプト案を3〜5個生成します  
>  
> 続けますか？」

---

## STEP 7: 案件一覧表示

「案件一覧を見せて」と言われた場合：

```bash
python scripts/project_cli.py list \
  --museum-dir "{MUSEUM_DIR}"
```

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `承認済みプロファイルが見つかりません` | オンボーディング実施を案内して中断 |
| `プロジェクトが既に存在します` | 既存案件を上書きしない。`status` サブコマンドで確認を促す |
| JSON パースエラー | 生の出力を担当者に提示してサポートを求める |
