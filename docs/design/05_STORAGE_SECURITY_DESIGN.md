# 05 保存・権限・障害復旧設計

文書日：2026年11月18日（Rev.2 2026年11月18日）  
文書区分：Phase 1 ストレージ・セキュリティ設計  
ステータス：Phase 1確定

---

## 1. 保存領域の定義

### 1.1 許可済み保存領域

| 領域 | パス | 用途 | 書き込み権限 |
|------|-----|------|------------|
| 製品リポジトリ | `exhibition-production-skills/` | 設計文書（Phase 1のみ） | 設計文書作成のみ |
| 館別データ領域 | `deployment.yaml` の `data_root` 以下 | 全てのSkills実行データ | Deployment Setup後に有効化 |

**一時ファイルの置き場：**  
`%TEMP%` は使用しない。一時ファイルは書き込み対象と**同一ディレクトリ**に生成する（§3.1で後述）。

**データ保存の正本：** ローカルファイル（クラウド同期や外部DBは許可外）

### 1.2 保存先パスの確定方法

Skillsは書き込み前に `deployment.yaml` を参照して保存先を確定する。

```
1. プロジェクトルートの deployment.yaml を読み込む
2. data_root を取得する
3. 対象の museum-id を組み合わせてターゲットパスを生成する
4. パス検証（§2）を通過した場合のみ書き込む
```

---

## 2. パス検証

すべての書き込み操作の前に以下を確認する。

### 2.1 検証手順

```python
from pathlib import Path

def validate_write_path(target_path: str, allowed_root: str) -> Path:
    target = Path(target_path).resolve()
    root = Path(allowed_root).resolve()

    # 1. 許可領域内かどうか確認（is_relative_to でパスの意味論的な比較を行う）
    #    str.startswith() は大文字小文字・末尾スラッシュの差異で誤判定する可能性がある
    try:
        target.relative_to(root)
    except ValueError:
        raise SecurityError(f"書き込み先が許可領域外: {target}")

    # 2. シンボリックリンクを経由していないか確認
    if target.is_symlink():
        raise SecurityError(f"シンボリックリンクへの書き込みは禁止: {target}")

    # 3. パス長確認（Windows MAX_PATH考慮）
    if len(str(target)) > 240:
        raise SecurityError(f"パスが長すぎます（240文字超）: {target}")

    return target
```

### 2.2 禁止パターン

- `..` を含むパス（パストラバーサル）
- 許可領域外のパス（`data_root` 外）
- シンボリックリンク経由のパス
- 240文字を超えるパス（Windows MAX_PATH考慮）

---

## 3. 書き込み安全性

### 3.1 アトミック書き込みプロトコル

**原則：** 一時ファイルは書き込み対象と**同一ディレクトリ**に生成する。  
理由：`os.replace()` はNTFS同一ボリューム内でのみアトミックが保証される。`%TEMP%` が別ドライブの場合は非アトミックになる。

```python
import os, tempfile, stat
from pathlib import Path

def atomic_write(target_path: Path, content: str) -> None:
    """
    アトミック書き込み：同一ディレクトリへの一時ファイル書き込み後リネーム。
    os.replace() は NTFS 同一ボリューム内でアトミックが保証される。
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 同一ディレクトリに一時ファイルを作成（同一ドライブ・同一ボリュームを保証）
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=target_path.parent,  # ← %TEMP% ではなく対象と同一ディレクトリ
        suffix='.tmp'
    )
    tmp_path = Path(tmp_path_str)

    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # 物理書き込み完了まで待機してからリネーム

        # 承認済みファイルへの上書き禁止（属性チェック）
        if target_path.exists():
            mode = os.stat(target_path).st_mode
            if not (mode & stat.S_IWRITE):
                raise PermissionError(
                    f"承認済みファイルへの直接上書きは禁止です: {target_path}\n"
                    f"改訂するには revision_in_progress フローを使用してください。"
                )

        os.replace(tmp_path, str(target_path))  # 同一ボリューム内でアトミック

    except Exception:
        # 失敗時は一時ファイルを必ず削除する
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
```

**障害シナリオと状態：**

| シナリオ | 発生後の状態 | 対処 |
|---------|-----------|------|
| 一時ファイルへの書き込み失敗 | `.tmp` 残留、原本無変更 | §3.2の起動時クリーンアップ |
| `os.replace()` 失敗（例外） | `.tmp` 削除、原本無変更 | ユーザーに通知 |
| プロセスクラッシュ（書き込み中） | `.tmp` 残留、原本無変更 | §3.2の起動時クリーンアップ |
| 承認済みファイルへの上書き試行 | PermissionError、`.tmp` 削除 | 改訂フロー案内 |

### 3.2 古い一時ファイルのクリーンアップ

起動時（Skill実行の最初の書き込み前）に古い `.tmp` ファイルをクリーンアップする。

**クリーンアップの安全条件：**  
次の**すべて**を満たす場合のみ削除を許可する。
1. ファイルの最終更新時刻が2時間以上前
2. 対応する本来のターゲットパス（`.tmp` 除いたパス）への書き込みが現在進行中でない

**条件2の確認方法：**  
`operation-log.yaml` の直近の `write` 操作を確認し、同一ターゲットパスへの操作が `success: null`（未完了）でないかを検証する。未完了エントリがある場合はクリーンアップを行わずユーザーに通知する。

```python
def cleanup_stale_tmp_files(directory: Path, max_age_hours: int = 2) -> list[Path]:
    """
    古い .tmp ファイルを削除する。安全条件を満たさない場合はスキップ。
    """
    import time
    removed = []
    for tmp_file in directory.rglob('*.tmp'):
        age_hours = (time.time() - tmp_file.stat().st_mtime) / 3600
        if age_hours >= max_age_hours:
            # ターゲットの書き込み進行中チェック（operation-log参照）
            if not _is_write_in_progress(tmp_file):
                tmp_file.unlink(missing_ok=True)
                removed.append(tmp_file)
    return removed
```

### 3.3 書き込み前の重複確認

すでに同名ファイルが存在する場合：

| ファイルの種類 | 動作 |
|-------------|------|
| 承認済みファイル（`status: approved`） | 書き込み禁止。改訂フローを案内 |
| 下書き・作業中ファイル | バックアップ作成後に上書き |
| 監査ログ | 追記のみ |

---

## 4. 承認済みファイルの保護（多層設計）

読み取り専用属性単独では属性解除後の変更を防げないため、以下の複数層を組み合わせる。

**改ざん防止の目標：**
- 誤操作による変更を防ぐ（第1層・第3層）
- 意図的な変更を検出して処理を中断する（第2層・第4層）
- 変更の事後調査を可能にする（第5層）

### 4.1 第1層：版固定ファイル名

承認時に `museum-profile-v{N}.yaml`（整数N）という版が明確なファイル名で保存する。  
「旧版ファイルを削除して新版を置く」操作を構造的に防止する。

### 4.2 第2層：SHA-256ハッシュによる整合性検証

承認時にファイル内容のSHA-256ハッシュを計算し、`artifact-manifest.yaml` に記録する。

```python
import hashlib

def compute_sha256(file_path: Path) -> str:
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_integrity(file_path: Path, manifest: dict) -> bool:
    actual = compute_sha256(file_path)
    expected = manifest.get('sha256', '')
    if actual != expected:
        raise IntegrityError(
            f"ファイルの整合性チェック失敗: {file_path}\n"
            f"  期待値: {expected}\n"
            f"  実際値: {actual}\n"
            f"  このファイルは承認後に変更された可能性があります。"
        )
    return True
```

**整合性チェックのタイミング：**
- 承認済みファイルを入力として読み込む前
- 承認済みファイルを出典・参照として使用する前

**ハッシュ不一致時の動作：** 処理を即座に中断し、ユーザーに通知する。自動修復はしない。

### 4.3 第3層：読み取り専用ファイル属性

承認時にWindowsファイル属性を読み取り専用に設定する（誤操作の抑止）。

```python
import stat

def protect_approved_file(file_path: Path) -> None:
    current = os.stat(file_path).st_mode
    os.chmod(file_path, current & ~stat.S_IWRITE)
```

属性解除後の変更はハッシュ検証（第2層）で検出する。

### 4.4 第4層：操作記録との照合

承認操作は `operation-log.yaml` に記録する。  
整合性チェック失敗時に操作記録を参照し、誰がいつ何を変更したかを調査できる。

### 4.5 改訂フロー

承認済みファイルを更新する場合は必ず以下のフローを経る：

```
1. ユーザーが改訂指示を出す
2. 対象の status を revision_in_progress に変更する
3. 旧バージョンを _backup/ にコピーする（バックアップの sha256 も記録）
4. 新しい下書き（-draft.yaml）を作成する
5. ヒアリング・編集・レビューを実施する
6. 再承認時に新版ファイル（v{N+1}）として保存し、ハッシュを再計算する
7. 読み取り専用属性を再設定する
```

---

## 5. バックアップ・復旧

### 5.1 バックアップのタイミング

| タイミング | 対象 | 保存先 |
|----------|------|--------|
| 承認済みファイルの改訂開始時 | 承認済みファイル | `{dir}/_backup/{filename}-{timestamp}` |
| 承認時（ドラフト保管） | 承認前のドラフト | `{dir}/_backup/{filename}-pre-approval-{timestamp}` |
| バックアップ作成時 | sha256も `_backup/backup-manifest.yaml` に記録 | — |

### 5.2 バックアップの保持方針

- バックアップは `_backup/` サブフォルダに保持する（製品が自動削除しない）
- 整理はユーザー・担当者が手動で実施する

### 5.3 復旧手順

```
1. エラーの種類を確認する
   a. .tmp ファイルが残っている → §3.2の条件を満たす場合のみ削除
   b. ファイル整合性エラー → _backup/ から sha256 が一致するバックアップを特定
   c. ファイルが削除された → _backup/ から最新バックアップを復元
2. operation-log で障害前後の操作履歴を確認する
3. バックアップから手動で復元する（製品は復元操作を支援するが自動化しない）
```

**展示制作の復旧優先度：**
1. `museum-profile-v{N}.yaml`（承認済みプロファイル）
2. `artifact-manifest.yaml`（成果物一覧・ハッシュ台帳）
3. 承認済み原稿・企画書
4. `source-registry.yaml`（出典台帳）

---

## 6. 監査ログ

以下の操作を `operation-log.yaml` に記録する。

| 操作 | 記録条件 |
|------|---------|
| ファイル書き込み | すべて |
| 承認・差し戻し | すべて |
| ハッシュ検証（成功・失敗） | すべて |
| バックアップ作成 | すべて |
| ファイル削除 | すべて（製品の操作） |
| エラー発生 | 書き込み失敗・検証エラー |

**ログの保存場所：** `{museum-id}/system/operation-log.yaml`（追記型）  
**MVP方針：** ログローテーションなし（追記のみ）。ファイルサイズ管理は将来の課題（OI-11）。

`operation-record` のスキーマは `03_DATA_MODEL_DESIGN.md` の§4.9を参照。

---

## 7. 競合検出

### 7.1 MVP の運用制約（単一書き込み主体）

**MVPでは同一館別データへの同時書き込みは発生しない前提とする。**

具体的には、同一の `{museum-id}` データに対して、Claude CodeとCodexを**同時に**使用する運用は想定しない。この制約はDeployment SetupのREADMEに明記する。

この前提が崩れる場合（複数担当者の同時作業等）は本節の設計を拡張する必要があり、その判断はPhase 7以降の課題とする。

### 7.2 競合検出：revision番号とハッシュによる楽観的制御

同一ファイルへの連続更新で意図しない上書きが発生しないよう、revision番号とハッシュで競合を検出する。

```python
def write_with_conflict_check(
    target_path: Path,
    new_content: str,
    expected_revision: int,
    expected_sha256: str
) -> None:
    """
    書き込み前に revision と sha256 を確認し、想定外の変更があれば中断する。
    """
    if target_path.exists():
        # revision チェック（artifact-manifest または YAMLヘッダから取得）
        current_revision = _read_revision(target_path)
        if current_revision != expected_revision:
            raise ConflictError(
                f"ファイルが想定外に更新されています（期待revision: {expected_revision}, "
                f"現在revision: {current_revision}）: {target_path}"
            )

        # ハッシュチェック（内容変更の有無を確認）
        current_sha256 = compute_sha256(target_path)
        if current_sha256 != expected_sha256:
            raise ConflictError(
                f"ファイルの内容が変更されています: {target_path}"
            )

    # 競合なし → アトミック書き込みを実行
    atomic_write(target_path, new_content)
```

### 7.3 updated_at の役割

`updated_at` フィールドは競合検出ではなく「最終更新の確認」と「ログ参照の補助」に使用する。  
revision番号とハッシュで競合を検出する設計とし、`updated_at` は主キーとして使用しない。

---

## 8. 権限レベルの定義

| 操作 | 条件 |
|------|------|
| museum-profileの読み込み | 常に許可。ただし承認済みファイルはハッシュ検証後に使用 |
| museum-profileの編集 | `draft` または `revision_in_progress` 状態のみ |
| museum-profileの承認 | ユーザーの明示的承認操作のみ（自動承認しない） |
| exhibition-projectの作成 | 承認済みprofileが存在し、ハッシュ検証が通る場合 |
| 承認済み成果物の変更 | 禁止（§4.5の改訂フロー経由のみ） |
| バックアップの削除 | ユーザーの明示的操作のみ（Skillは実行しない） |
| `data_root` 外への書き込み | 禁止 |
| 外部サービスへの送信 | ユーザー確認後、目的と宛先を説明してから実行 |

---

## 9. データ区分とAI入力制限

ローカル保存とAIモデルへの非送信は同義ではない。

**AI入力制限チェックのタイミング：**  
データをAIへの入力として渡す**前**（書き込み前ではなく読み込み・生成前）に確認する。

| データ区分 | デフォルト | 設定可能 |
|-----------|----------|---------|
| 設定ファイル（deployment.yaml） | AI入力可 | — |
| museum-profile | AI入力可 | 館が制限可能 |
| 調査メモ・企画書 | AI入力可 | 館が制限可能 |
| 許諾なし原資料（写真・文書等） | AI入力禁止 | 館の明示許可で解除可 |
| 個人情報を含むデータ | AI入力禁止 | 変更不可（共通安全制約） |

AI入力制限の設定は `museum-profile.data_management.ai_input_restrictions` に記録する。  
Skillsはデータを読み込んでAIへ渡す前に制限リストを確認し、制限対象のデータは処理しない。
