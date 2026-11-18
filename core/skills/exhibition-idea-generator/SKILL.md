---
name: exhibition-idea-generator
description: 展示プロジェクトのコンセプト案（アイディア）を3〜5個生成し、比較・選定を行う。「アイディアを生成して」「コンセプト案を出して」「展示の案を考えて」「idea generator」と依頼されたときに起動する。
---

# Exhibition Idea Generator

## 責務

展示プロジェクトのブリーフ情報と館別プロファイルを元に **コンセプト案（IdeaEntry）を3〜5個** 提案し、担当者が1つを選定できるようにする。

## 実行ルール（必ず守る）

1. **担当者が選定を確認するまで `select` を実行しない**
2. **却下済みアイディアを再度提案しない**
3. **選定後は exhibition-director または次フェーズへ引き継ぐ**
4. **生成したアイディアは必ず idea_cli.py 経由で保存する**

---

## STEP 0: 環境確認

### 0-1. deployment.yaml の読み込み

プロジェクトルートの `deployment.yaml` を Read ツールで読み込む。

- 見つからない場合 → 「`/exhibition-deployment-setup` を先に実行してください」と伝えて中断する

`data_root` の値を **DATA_ROOT** として記憶する。

### 0-2. project_id・museum_id の確認

担当者に確認する（会話で既出の場合はスキップ）：

> 「対象の案件IDと館IDを教えてください。  
> （例：案件ID `project-20260401`、館ID `museum-001`）」

**MUSEUM_ID**, **PROJECT_ID** を記憶する。  
**MUSEUM_DIR** = `{DATA_ROOT}/{MUSEUM_ID}`  
**PROJECT_DIR** = `{MUSEUM_DIR}/{PROJECT_ID}`  
**PROJECT_PATH** = `{PROJECT_DIR}/exhibition-project.yaml`

---

## STEP 1: プロジェクト情報の読み込み

```bash
python scripts/project_cli.py status \
  --project-path "{PROJECT_PATH}"
```

失敗した場合 → 「`/exhibition-director` で先に案件を作成してください」と伝えて中断する。

PROJECT_STATUS の `brief`（theme, target_visitors, period, constraints）を記憶する。

---

## STEP 2: 館別プロファイルの読み込み

```bash
python scripts/project_cli.py check-prerequisites \
  --museum-dir "{MUSEUM_DIR}"
```

`profile_path` を取得し、Read ツールで館別プロファイルを読み込む。  
コレクションの強み・特別展実績・来館者層を把握する。

---

## STEP 3: 既存アイディアの確認

```bash
python scripts/idea_cli.py status \
  --project-dir "{PROJECT_DIR}"
```

- `has_ideas: false` の場合 → idea-list を新規作成してからアイディア生成へ（STEP 4）
- `selected_idea_id` が設定済みの場合 → 「既に選定済みのアイディアがあります」と伝え、STEP 7へ
- アイディアはあるが未選定の場合 → 既存アイディアを提示し、追加生成か選定作業かを担当者に確認する

---

## STEP 4: idea-list の作成（新規の場合のみ）

```bash
python scripts/idea_cli.py create \
  --project-path "{PROJECT_PATH}" \
  --brief-summary "{BRIEF_SUMMARY}"
```

---

## STEP 5: アイディア生成

プロジェクトのブリーフ・館プロファイル・制約条件を踏まえ、**3〜5個のコンセプト案**を考案する。

各アイディアには以下を含める：

| 項目 | 内容 |
|------|------|
| `id` | `idea-01`, `idea-02` ... |
| `title` | 展示タイトル案（20字以内） |
| `concept` | コンセプト説明（100字以内） |
| `key_themes` | 主要テーマキーワード 3〜5個 |
| `unique_points` | 他の展示との差別化ポイント 2〜3個 |
| `target_visitors` | 主なターゲット来館者層 |
| `estimated_duration` | 展示鑑賞の目安所要時間 |

担当者にアイディア一覧を提示する（Markdown 形式）：

```
## コンセプト案

### 案1：{title}
**コンセプト**：{concept}
**主要テーマ**：{key_themes}
**ユニークポイント**：{unique_points}
**対象来館者**：{target_visitors}
**所要時間目安**：{estimated_duration}

... (案2〜5も同様)
```

---

## STEP 6: アイディアの保存

担当者の確認後（「内容を確認しました」「次へ」など）、各アイディアを保存する。

各アイディアに対して：

```bash
python scripts/idea_cli.py add \
  --project-dir "{PROJECT_DIR}" \
  --idea-json '{"id":"idea-01","title":"...","concept":"...","key_themes":[...],"unique_points":[...],"target_visitors":[...],"estimated_duration":"..."}'
```

保存後、比較表（`ideas/comparison.md`）が自動生成される。

---

## STEP 7: アイディア選定

担当者に選定を促す：

> 「{N}個のコンセプト案を提案しました。  
> どの案を採用しますか？（案番号または案名でお伝えください）  
> また、変更・追加の希望があればお知らせください。」

担当者が選定を確定したら（「案2にします」「idea-03で」など）：

```bash
python scripts/idea_cli.py select \
  --project-dir "{PROJECT_DIR}" \
  --idea-id "idea-0N"
```

却下したいアイディアがある場合：

```bash
python scripts/idea_cli.py reject \
  --project-dir "{PROJECT_DIR}" \
  --idea-id "idea-0N" \
  --reason "{REJECTION_REASON}"
```

---

## STEP 8: 完了報告

> 「コンセプト案「{SELECTED_TITLE}」を採用しました。  
>  
> 比較表は `{PROJECT_DIR}/ideas/comparison.md` に保存されています。  
>  
> 次のステップとして、このコンセプトを元に詳細なコンテンツ設計を進めることができます。  
> 続けますか？」

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `却下済みのアイディアは選定できません` | 担当者に別の案を選ぶよう促す |
| `選定済みのアイディアは却下できません` | 先に別のアイディアを選定するよう案内する |
| `アイディアIDが重複しています` | ID を `idea-0N` → `idea-{N+10}` などに変更して再試行する |
| JSON パースエラー | 生の出力を担当者に提示してサポートを求める |
