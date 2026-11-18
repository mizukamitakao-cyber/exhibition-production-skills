# 09 未決事項・リスク・判断事項

文書日：2026年11月18日（Rev.2 2026年11月18日）  
文書区分：Phase 1 未決事項  
ステータス：Phase 1設計完了時点

---

## 凡例

- **影響度**：高（設計変更が必要）/ 中（実装方針に影響）/ 低（後続Phaseで確認可）
- **種別**：判断（人間が決定）/ 調査（技術確認が必要）/ 仕様待ち（外部依存）

---

## 未決事項一覧

| ID | 課題 | 影響度 | 種別 | 推奨アクション | 判断期限 |
|----|------|--------|------|--------------|---------|
| OI-01 | Claude Codeのプロジェクトレベルスキル配置（`.claude/skills/`）の動作確認 | 高 | 調査 | テストスキルを `.claude/skills/exhibition-oi01-test/` に配置済み。次回セッション開始時に `/exhibition-oi01-test` で動作確認する | Phase 3実装前 |
| OI-04 | デプロイスクリプトの実行タイミング（手動 vs 自動トリガー） | 中 | 判断 | 手動実行を基本とし、CLAUDE.mdのフックで補助 | Phase 2設計時 |
| OI-06 | 承認済みファイルの多層保護実装の詳細仕様（版管理ファイル名形式・SHA-256保存場所） | 中 | 調査 | Phase 3実装前に保護ロジックの詳細を設計する | Phase 3実装前 |
| OI-07 | Museum Onboardingの質問言語（日本語固定 vs 設定可能） | 低 | 判断 | 日本語固定で開発し、Phase後期に多言語対応を検討 | Phase 2設計時 |
| OI-08 | 展示制作テンプレートの初期版（歴史館・美術館・自然史館の3分野を想定） | 低 | 判断 | 歴史館1館分の架空データでMVP検証後に他分野追加 | Phase 3実装前 |
| OI-09 | `exhibition-production-data/`のGit管理有無（館ごとの判断） | 低 | 判断 | 基本方針は非Git、館の判断に委ねる。READMEで選択肢を提示 | Phase 2実装前 |
| OI-10 | Deployment SetupのGUI vs CUI（Claude Code対話 vs Pythonスクリプト） | 低 | 判断 | Claude Code対話型を主とし、Pythonスクリプトを補助に配置 | Phase 2設計時 |
| OI-11 | Codex固有のSkills/Tools実行機構の有無（SKILL.md相当機能が存在するか） | — | ~~調査~~ | **解決済み（Phase 2）** `adapters/codex/README.md` 参照 | — |
| OI-12 | `common-settings.yaml`のスキーマ定義（4階層上位から下位への制約継承ルール） | 中 | 調査 | Phase 2のPydanticモデル実装時（タスク2-04）に設計する | Phase 2実装中 |
| OI-13 | `questions.yaml`のフォーマット仕様確定（ドメイン追加手順・必須フィールドの確定） | 中 | 調査 | Phase 3のMuseum Onboardingスキル実装前（タスク3-03）に確定する | Phase 3実装前 |

**解決済み（Phase 1承認により決定）：**

| ID | 課題 | 決定内容 |
|----|------|---------|
| OI-03 | YAML検証ライブラリの選定 | `pydantic v2` を採用。JSON SchemaはPydanticモデルから自動生成 |
| OI-05 | 館別データパスの設定方式 | `deployment.yaml` を採用。`deployment.yaml.template`（Git管理）と`deployment.yaml`（gitignore）を分離 |

**解決済み（Phase 2実装中）：**

| ID | 課題 | 決定内容 |
|----|------|---------|
| OI-02 | Codex AGENTS.mdの制約 | 上限32KiB。11スキル分の指示（~7KB）は余裕で収まる |
| OI-11 | Codex固有のSkills実行機構 | Agent Skills open standard 対応。SKILL.mdフォーマット共通。配置先は `.agents/skills/`。`adapters/codex/README.md` に詳細記録 |

---

## 設計上の仮定（後続Phaseで検証が必要）

| ID | 仮定内容 | 検証方法 |
|----|---------|---------|
| AS-01 | Claude Codeはプロジェクトレベルの`.claude/skills/`を認識する | Phase 2で動作確認スクリプト実行（OI-01） |
| AS-02 | Python `pathlib.Path`でWindows/Unixのパス差異を吸収できる | Phase 2のスクリプト実装時に確認 |
| AS-03 | `pydantic v2`でYAMLスキーマ検証が実用的に動作する | Phase 2のスキーマ実装時に確認 |
| AS-04 | Codex VS CodeはAGENTS.md（指示層）を認識し、MuseumOnboarding規模の指示を処理できる | Phase 2のCodex仕様調査（タスク2-11）とAT-10 Liteで確認 |
| AS-05 | NTFS上で`os.replace()`によるアトミック書き込みが同一ドライブ内で機能する | Phase 2のアトミック書き込み単体テスト（タスク2-13）で確認 |

---

## 既知リスク

| ID | リスク | 発生確率 | 影響 | 対応策 |
|----|--------|---------|------|--------|
| R-01 | Claude CodeのSkills仕様変更（バージョンアップによる破壊的変更） | 中 | 高 | スキルの核はMarkdownで記述し、フォーマット依存を最小化 |
| R-02 | 過剰設計による実装工数増大 | 高 | 中 | Phase 2はMVP（Museum Onboarding + Director）のみに絞る |
| R-03 | 館別データの誤上書きによる原本破損 | 低 | 高 | 版管理ファイル名・SHA-256・読み取り専用属性・監査ログの4層で防止 |
| R-04 | Windowsのパス長制限（MAX_PATH 260文字）によるエラー | 中 | 中 | ディレクトリ名を短く設計、`museum-001/`形式のID採用 |
| R-05 | Codex AGENTS.mdの文字数制限によりSkill全量を統合できない | 中 | 中 | Phase 2初期にOI-02・OI-11を調査し、制限が明らかになった時点でP0 Skills優先・P1はオプション化する設計に切り替える |
| R-06 | Codex固有のSkills実行機構が存在せず、実行層アダプターの設計前提が崩れる | 中 | 高 | Phase 2初期にOI-11を確認。機構が存在しない場合はClaude Code専用製品として先行し、Codex対応をPhase 7以降に延期する |

---

## Phase 2開始前に解決すべき事項

以下はPhase 2の実装設計前に確認・実施が必要な事項：

1. **OI-01**：Claude Codeプロジェクトレベルスキルの動作検証（Phase 2タスク2-12）
2. **OI-11**：Codex Skills/Tools実行機構の有無を確認（Phase 2タスク2-11、OI-02と同時調査）
3. **OI-09**：館別データディレクトリのGit管理方針をREADMEに記載

**OI-03・OI-05 は Phase 1承認時に解決済み。**
