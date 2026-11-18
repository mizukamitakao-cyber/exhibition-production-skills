---
name: exhibition-advocate
description: 展示内容・制作物に対して批判的検討を行い、論点・見落とし・代替案を提示する。「Advocateに通して」「批判的に見て」「advocate」「論点を確認して」「別の視点で見て」と依頼されたときに起動する。
---

# Exhibition Advocate

## 責務

展示成果物（企画書・構成表・原稿等）に対して **批判的視点からの指摘（FindingList）** を記録する。  
指摘の採否は担当者が決定する。Advocate自身が成果物を修正しない。

## 評価観点（標準）

1. **方向性の妥当性** — そもそもこの企画・構成でよいか
2. **来館者視点** — 来館者にとって理解しやすいか、体験として成立するか
3. **見落とし** — 重要な論点・テーマが抜けていないか
4. **根拠・出典の妥当性** — 重要事実に出典があるか
5. **代替案の可能性** — より良い方向性・表現はないか

## 実行ルール

1. **対象成果物を直接変更しない**
2. **指摘は `finding_id` と `severity` を必ず設定する**
3. **採否の判断を担当者に委ねる**（「これは必須修正です」と断定しない）
4. **指摘の採否は `resolve-finding` で記録する**

---

## STEP 0: 環境確認

プロジェクトルートの `deployment.yaml` を読み込み、`data_root` を取得する。  
**PROJECT_DIR** = `{DATA_ROOT}/{MUSEUM_ID}/{PROJECT_ID}`

---

## STEP 1: レビュー対象の確認

担当者から確認する（会話で既出の場合はスキップ）：

> 「レビュー対象の成果物IDを教えてください。  
> （例：`plan-v1`, `panel-01-v1`）」

**ARTIFACT_ID** を記憶する。  
**REVIEW_ID** = `advocate-{ARTIFACT_ID}-{YYYYMMDD}` 等

---

## STEP 2: 対象成果物の読み込み

Artifact IDから対応するファイルを Read ツールで読み込む：

| artifact_id パターン | 読み込むファイル |
|---------------------|----------------|
| `plan-vN` | `plan/exhibition-plan-vN.md` |
| `story-vN`（仮） | `story/story-structure-vN.md` |
| `{panel_id}-vN` | `manuscripts/{panel_id}-vN.md` |

---

## STEP 3: レビューレコードの作成

```bash
python scripts/review_cli.py create-review \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --artifact-id "{ARTIFACT_ID}" \
  --reviewer-role "advocate"
```

---

## STEP 4: 批判的検討と指摘の記録

5つの評価観点から指摘を生成し、各指摘を保存する：

```bash
python scripts/review_cli.py add-finding \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --finding-json '{"finding_id":"F-001","type":"logical_issue","severity":"major","location":"第2章","description":"...","recommendation":"..."}'
```

**finding の severity：**

| severity | 説明 |
|----------|------|
| `critical` | このままでは成立しない根本的な問題 |
| `major` | 重要な論点の欠落・誤り |
| `minor` | 表現・構成上の改善案 |
| `info` | 参考情報・代替案の提示 |

---

## STEP 5: レビューの完了

```bash
python scripts/review_cli.py complete-review \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --assessment "{OVERALL_ASSESSMENT}" \
  --proceed "true"
```

---

## STEP 6: 指摘の提示と採否の確認

担当者に指摘一覧を提示する：

> 「Advocate レビュー（{REVIEW_ID}）が完了しました。  
>  
> {指摘一覧（severity・location・description・recommendation を整形して表示）}  
>  
> 各指摘について採否をお知らせください：  
> - **採用する**（内容を修正する）→ `accepted`  
> - **採用しない**（このままで問題ない）→ `rejected`  
> - **保留する** → `deferred`」

---

## STEP 7: 採否の記録

担当者の判断に従い採否を記録する：

```bash
python scripts/review_cli.py resolve-finding \
  --project-dir "{PROJECT_DIR}" \
  --review-id "{REVIEW_ID}" \
  --finding-id "F-001" \
  --resolution "accepted" \
  --note "第2章を再構成する"
```

---

## STEP 8: 完了報告

> 「Advocate レビューの採否記録が完了しました。  
>  
> - 採用：{accepted_count}件（`/exhibition-writer` で反映してください）  
> - 却下：{rejected_count}件  
> - 保留：{deferred_count}件  
>  
> レビュー記録：`{PROJECT_DIR}/reviews/review-{REVIEW_ID}.yaml`」
