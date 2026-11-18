---
name: exhibition-museum-onboarding
description: 館の特性をヒアリングし、館別プロファイル（museum-profile.yaml）を作成・承認する。「オンボーディング」「館のプロファイル作成」「ヒアリング」「museum onboarding」「プロファイル作成」「館の設定」と依頼されたとき、またはDeployment Setupの完了後に「オンボーディングを開始して」と依頼されたときに起動する。
---

# Exhibition Museum Onboarding

## 責務

館の担当者との対話を通じて **館別プロファイル（museum-profile-vN.yaml）** を作成・承認する。

## 実行ルール（必ず守る）

1. **1回の返答で提示する質問は最大3問**
2. **確認済みの質問は重複して聞かない**（answered_questions を必ず確認する）
3. **毎回の対話後に onboarding-session.yaml を保存する**（Bash ツール経由）
4. **AIの提案を担当者の確認なしに正式設定として登録しない**
5. **「中断」「後で続ける」と言われたら即座に pause して終了する**

---

## STEP 0: 環境確認

### 0-1. deployment.yaml の読み込み

プロジェクトルートの `deployment.yaml` を Read ツールで読み込む。

- 見つからない場合 → 「`/exhibition-deployment-setup` を先に実行してください」と伝えて中断する

`data_root` の値を **DATA_ROOT** として記憶する。

### 0-2. questions.yaml の読み込み

`references/questions.yaml` を Read ツールで読み込む（このファイルはスキルの参照ファイルとして同梱されている）。
フェーズ一覧と質問定義を記憶する。

---

## STEP 1: museum_id の確定

担当者に確認する：

> 「この館の識別子（museum_id）を設定します。  
> 推奨形式：`museum-001`（半角英数字とハイフンのみ）  
> 希望の識別子を教えてください（そのまま使用します）。  
> なければ `museum-001` を提案します。」

確定した museum_id を **MUSEUM_ID** として記憶する。

**MUSEUM_DIR** = `{DATA_ROOT}/{MUSEUM_ID}`

---

## STEP 2: 既存セッションの確認

**SESSION_PATH** = `{MUSEUM_DIR}/onboarding-session.yaml`

Bash ツールで確認する：

```bash
python scripts/onboarding_cli.py status --session-path "{SESSION_PATH}" 2>/dev/null || echo "NO_SESSION"
```

### セッションが存在する場合（再開）

ステータス JSON を解析する。

- `status` が `paused` の場合：
  > 「前回のセッションが中断されています（{paused_at} 中断、理由：{paused_reason}）。  
  > 続きから再開しますか？」

  「はい」の場合：

  ```bash
  python scripts/onboarding_cli.py resume --session-path "{SESSION_PATH}"
  ```

- `status` が `in_progress` の場合：
  > 「セッションが進行中です（{current_phase} フェーズ、{answered_count} 問回答済み）。続けます。」

- `status` が `ready_for_review` または `approved` の場合：
  > 「このIDのプロファイルは既に{status}状態です。改訂する場合は担当者の指示を待ちます。」  
  中断する。

### セッションが存在しない場合（新規）

データディレクトリを作成してセッションを作成する：

```bash
python -c "from pathlib import Path; Path(r'{MUSEUM_DIR}').mkdir(parents=True, exist_ok=True); print('OK')"
```

```bash
python scripts/onboarding_cli.py create --museum-id "{MUSEUM_ID}" --session-id "session-001" --session-path "{SESSION_PATH}"
```

---

## STEP 3: ヒアリング

**QUESTIONS_PATH** = `references/questions.yaml`

現在のセッション状態を読み込み、**ヒアリングループ** を実行する。

### ループ開始前の確認

```bash
python scripts/onboarding_cli.py status --session-path "{SESSION_PATH}"
```

`current_phase` を確認し、そのフェーズの質問へ進む。

### ヒアリングループ（1ターン = 1〜3問）

#### A. 次の質問を取得する

```bash
python scripts/onboarding_cli.py next-questions \
  --session-path "{SESSION_PATH}" \
  --questions-path "{QUESTIONS_PATH}" \
  --count 3
```

返却された `questions` リストが空で `current_phase` も空の場合 → STEP 4 へ進む。

#### B. 質問を提示する

取得した質問を担当者に提示する。フェーズ名（display_name）を見出しとして表示する。

例：
> 「**【基本情報】** 次の質問にお答えください（1〜3問）：  
> 1. 館の正式名称を教えてください。  
> 2. 施設の種別はどれですか（博物館・資料館・文化施設・その他）。  
> 3. 施設の設置目的・使命を一言で表すと何でしょうか？」

#### C. 回答を記録する

担当者が回答したら、各質問IDに対して記録する：

```bash
python scripts/onboarding_cli.py record-answer \
  --session-path "{SESSION_PATH}" \
  --question-id "B-01" \
  --answer "{回答テキスト}"
```

**重要：** 担当者が「不明」「後で」「スキップ」と回答した場合は record-answer ではなく skip を使う：

```bash
python scripts/onboarding_cli.py skip \
  --session-path "{SESSION_PATH}" \
  --question-id "B-01" \
  --reason "{理由}"
```

#### D. フェーズ完了チェック

各回答記録後にフェーズの完了状態を確認する：

```bash
python scripts/onboarding_cli.py check-phase \
  --session-path "{SESSION_PATH}" \
  --phase-name "{current_phase}" \
  --questions-path "{QUESTIONS_PATH}"
```

`is_complete` が `true` の場合、フェーズを完了して次へ進む：

```bash
python scripts/onboarding_cli.py complete-phase \
  --session-path "{SESSION_PATH}" \
  --phase-name "{current_phase}" \
  --questions-path "{QUESTIONS_PATH}"
```

> 「**{フェーズ名}フェーズ完了です。** 次は {次フェーズ名} についてお聞きします。」

担当者が「このフェーズをスキップ」と言った場合も complete-phase を実行して次へ進む。

#### E. 中断処理

担当者が「中断」「後で続ける」「今日はここまで」と言った場合：

```bash
python scripts/onboarding_cli.py pause \
  --session-path "{SESSION_PATH}" \
  --reason "担当者が中断を指示"
```

> 「セッションを保存しました。次回 `/exhibition-museum-onboarding` を実行すると続きから再開できます。  
> 現在の進捗：{completed_phases} 完了、{current_phase} 途中。」

**そのままスキルを終了する。**

#### F. ループ継続

STEP 3-A に戻り、ループを続ける。全フェーズの必須質問が完了すると session_status が `ready_for_review` になる。

---

## STEP 4: プロファイルドラフトの生成

**DRAFT_PATH** = `{MUSEUM_DIR}/museum-profile-draft.yaml`

```bash
python scripts/onboarding_cli.py build-profile \
  --session-path "{SESSION_PATH}" \
  --questions-path "{QUESTIONS_PATH}" \
  --draft-path "{DRAFT_PATH}"
```

生成されたドラフトを Read ツールで読み込み、全フィールドを担当者に一覧提示する。

---

## STEP 5: 担当者レビュー

以下を提示する：

> 「以下がヒアリング結果から作成した館別プロファイルです。内容を確認してください。  
> （全項目一覧を表示）  
>   
> 修正が必要な箇所はありますか？  
> なければ「承認」とお伝えください。」

### 修正あり

担当者が修正を指示した場合：
- 該当質問IDに対して record-answer を再実行する
- build-profile を再実行してドラフトを更新する
- 担当者に再提示する

### 承認

担当者が「承認」「OK」「これで確定」と言った場合 → STEP 6 へ

---

## STEP 6: 承認・保護

承認者名を確認する：

> 「承認者のお名前を教えてください（任意、省略可）。」

```bash
python scripts/approval_cli.py approve \
  --museum-dir "{MUSEUM_DIR}" \
  --draft-path "{DRAFT_PATH}" \
  --approved-by "{承認者名またはnull}"
```

出力 JSON の `versioned_path` を確認する。

---

## STEP 7: 完了メッセージ

> 「館別プロファイルを承認・保護しました。  
>   
> - 保存先：`{versioned_path}`  
> - 状態：読み取り専用（誤操作保護）  
> - SHA-256ハッシュ：`profile-manifest.yaml` に記録済み  
>   
> 次のステップ：展示企画を開始する場合は `/exhibition-director` を実行してください。」

---

## セッション再開時の案内（長期中断後）

中断から1週間以上経過している場合（paused_at と現在日時の差を確認）、主要な回答内容を要約して確認を促す：

> 「前回のセッションから時間が経っています。主な回答内容を確認します：  
> - 館名：{basic.name}  
> - 専門分野：{basic.domains}  
> - 文体：{writing.style}  
> ...  
> 変更がある場合は教えてください。」

---

## エラー対応

| 状況 | 対応 |
|------|------|
| SESSION_PATH への書き込み失敗 | エラーを提示し、`pause` を試みる。失敗なら手動保存方法を案内する |
| build-profile エラー | エラーメッセージを提示し、問題の質問IDを特定して再入力を求める |
| approve エラー | エラーメッセージを提示し、担当者に確認を求める（ファイル権限の問題の可能性） |
| questions.yaml が見つからない | 「スキルの参照ファイルが見つかりません。スキルを再インストールしてください（`python scripts/deploy.py`）」と案内する |
