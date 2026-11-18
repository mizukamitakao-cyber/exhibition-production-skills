---
name: exhibition-deployment-setup
description: 企画展示制作AI Skillsの初期セットアップを行う。deployment.yamlを作成し、スキルをインストールする。「セットアップ」「deployment setup」「初期設定」「インストール」「セットアップして」と依頼されたときに起動する。
---

# Exhibition Deployment Setup

## 責務

初めてこのシステムを使う環境で `deployment.yaml` を作成し、Skillsを所定のディレクトリへインストールする。

## 実行ルール

- 既存の `deployment.yaml` がある場合は上書きしない（内容を読み上げ、更新か確認する）
- パスは担当者が入力した値をそのまま使う。推測で埋めない
- インストール後、動作確認まで完了してから終了する

---

## STEP 0: 既存設定の確認

プロジェクトルートの `deployment.yaml` を Read ツールで試みる。

- **存在する場合** → 現在の設定を読み上げ、「更新しますか？」と確認する。更新の場合は STEP 2 へ（既存値を初期値として提示）
- **存在しない場合** → STEP 1 へ

---

## STEP 1: Python環境確認

Bash ツールで実行する：

```bash
python --version
```

Python 3.11以上が必要。なければインストールを案内して中断する。

```bash
python -c "import pydantic; from ruamel.yaml import YAML; print('依存OK')"
```

失敗した場合：

```bash
pip install -r requirements.txt
```

---

## STEP 2: データ保存先の設定

担当者に質問する：

> 「展示制作データの保存先ディレクトリを教えてください。  
> 例：`C:/Users/yamada/Documents/exhibition-data`  
> （Googleドライブなど同期ツールのフォルダも可能です）」

受け取ったパスを `DATA_ROOT` として記憶する。

---

## STEP 3: 専門分野の設定

担当者に質問する：

> 「取り扱う専門分野を教えてください（複数可、読点区切り）：  
> - 歴史 (history)  
> - 美術 (art)  
> - 自然史 (natural-history)  
> - 科学 (science)」

選択された分野をリストとして記憶する。

---

## STEP 4: AI環境の確認

担当者に質問する：

> 「使用するAI環境を教えてください（複数可）：  
> 1. Claude Code のみ  
> 2. Claude Code + Codex（VS Code）」

---

## STEP 5: OSの検出

Bash ツールで実行する：

```bash
python -c "import platform; print(platform.system().lower())"
```

---

## STEP 6: deployment.yaml の作成

取得した情報を元に `deployment.yaml` を Write ツールで作成する。
専門分野は各行の先頭に `  - ` を付けてリスト形式で記述する。

```yaml
product_version: "0.1.0"
data_root: "{DATA_ROOT}"
skills_root: "~/.claude/skills"
domains:
  - {選択された分野1}
  - {選択された分野2}
environment:
  os: "{os}"
  ai_tools:
    - claude-code
deployment:
  deployed_at: null
  deployed_by: null
  last_updated: null
```

---

## STEP 7: データディレクトリの作成

Bash ツールで実行する：

```bash
python -c "from pathlib import Path; p = Path(r'{DATA_ROOT}'); p.mkdir(parents=True, exist_ok=True); print(f'作成: {p}')"
```

---

## STEP 8: スキルのインストール

Bash ツールで実行する：

```bash
python scripts/deploy.py
```

出力を確認し、インストールされたスキル一覧を担当者に提示する。

---

## STEP 9: 動作確認

Bash ツールで実行する：

```bash
python -c "
import sys; sys.path.insert(0, '.')
from core.config import load_deployment_config
config = load_deployment_config('deployment.yaml')
print(f'data_root: {config.data_root}')
print('設定読み込み OK')
"
```

---

## STEP 10: 導入記録の更新

Bash ツールで現在日時を取得して `deployment.yaml` の `deployment` セクションを Edit ツールで更新する：

```bash
python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat())"
```

---

## 完了メッセージ

> 「セットアップ完了です。次は館別プロファイルを作成します。  
> 「オンボーディングを開始して」と話しかけると  
> `/exhibition-museum-onboarding` が起動します。」

---

## エラー対応

| エラー | 対応 |
|-------|------|
| Python が見つからない | Python 3.11 以上のインストールを案内する |
| pydantic / ruamel.yaml がない | `pip install -r requirements.txt` を案内する |
| パスに日本語 | 警告を出しつつ、英数字パスへの変更を推奨する |
| deployment.yaml 書き込み失敗 | 手動作成の手順を案内する |
| scripts/deploy.py 失敗 | エラー内容を提示し、手動インストール手順（`~/.claude/skills/` へのコピー）を案内する |
