---
name: exhibition-reviewer
description: 成果物が要件・基準を満たしているかを検証し、問題点を指摘する。「Reviewerに通して」「要件チェックをして」「reviewer」「文字数を確認して」「出典の確認をして」と依頼されたときに起動する。
---

# Exhibition Reviewer

## 責務

展示成果物（原稿・企画書等）が要件・基準を満たしているかを **客観的に検証** し、問題点を記録する。  
Advocate が「方向性・内容」を見るのに対し、Reviewer は「要件への適合・正確性」を見る。  
指摘の採否は担当者が決定する。Reviewer自身が成果物を修正しない。

## 評価観点（標準）

1. **事実の正確性** — 重要事実に出典があるか
2. **表記・用語の統一** — 館プロファイルの用語集・文体規程への適合
3. **文字数・形式要件** — 規程に収まっているか
4. **権利・利用許諾** — 画像・引用の利用許諾が確認されているか
5. **プロファイル要件への適合** — 対象来館者・言語・難易度が合致しているか

## 実行ルール

1. **対象成果物を直接変更しない**
2. **客観的な要件違反のみを `major/critical` として記録する**（主観的な好みは `info` または省略）
3. **採否の判断は担当者に委ねる**
4. **指摘の採否は `resolve-finding` で記録する**

---

## STEP 0: 環境確認

プロジェクトルートの `deployment.yaml` を読み込み、`data_root` を取得する。  
**PROJECT_DIR** = `{DATA_ROOT}/{MUSEUM_ID}/{PROJECT_ID}`

---

## STEP 1: レビュー対象の確認

担当者から確認する：

> 「レビュー対象の成果物IDを教えてください。  
> （例：`plan-v1`, `panel-01-v1`）」

**ARTIFACT_ID** を記憶する。  
**REVIEW_ID** = `reviewer-{ARTIFACT_ID}-{YYYYMMDD}` 等

---

## STEP 2: 対象成果物と要件の読み込み

対象ファイルを Read ツールで読み込む（表を参照）。

また、以下も読み込む：
- 館別プロファイル（`museum-profile-vN.yaml`）の `writing` セクション
- 出典台帳（`research/source-registry.yaml`）

---

## STEP 3: レビューレコードの作成

```bash
python scripts/review_cli.py create-review \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --artifact-id "{ARTIFACT_ID}" \
  --reviewer-role "reviewer"
```

---

## STEP 4: 要件検証と指摘の記録

以下の観点を順番に確認し、問題があれば指摘を記録する：

### 4-1. 文字数チェック

原稿の文字数をカウントし、館プロファイルの制限と照合する。

```bash
python scripts/review_cli.py add-finding \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --finding-json '{"finding_id":"R-001","type":"requirement_gap","severity":"major","location":"パネル全体","description":"文字数 {actual}字が制限 {limit}字を超過しています","recommendation":"{actual - limit}字の削減が必要です"}'
```

### 4-2. 出典確認

重要事実の記述に `source_id` の参照があるか確認する。  
出典台帳（`source-registry.yaml`）で未確認（`unverified`）の出典を参照していないか確認する。

### 4-3. 表記・用語確認

館プロファイルの用語集（`writing.terminology`）と照合する。

### 4-4. 対象来館者レベルの確認

表現の難易度が来館者プロファイルに合致しているか確認する。

---

## STEP 5: レビューの完了

```bash
python scripts/review_cli.py complete-review \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --assessment "{OVERALL_ASSESSMENT}" \
  --proceed "{true|false}"
```

`proceed: false` は `critical` または `major` 指摘が未解決の場合に設定する。

---

## STEP 6: 指摘の提示と採否の確認

担当者に指摘一覧を提示する（Advocateと同様の形式）。

---

## STEP 7: 採否の記録

```bash
python scripts/review_cli.py resolve-finding \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --finding-id "R-001" \
  --resolution "accepted" \
  --note "文字数を削減します"
```

---

## STEP 8: 完了報告

> 「Reviewer レビューの採否記録が完了しました。  
>  
> - 採用：{accepted_count}件  
> - 却下：{rejected_count}件  
> - 保留：{deferred_count}件  
>  
> `proceed_recommendation: {true|false}`  
> レビュー記録：`{PROJECT_DIR}/reviews/review-{REVIEW_ID}.yaml`」

---

## 継続方針

- `critical/major` 指摘が `accepted` の場合 → `exhibition-writer` で反映
- `rejected/deferred` のみの場合 → 次フェーズへ進む判断は担当者が行う
