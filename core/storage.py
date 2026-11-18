"""
保存・パス検証・アトミック書き込み・競合検出
設計仕様: docs/design/05_STORAGE_SECURITY_DESIGN.md
"""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


class SecurityError(Exception):
    pass


class ConflictError(Exception):
    pass


def validate_write_path(target_path: str, allowed_root: str) -> Path:
    """書き込みパスを検証し、安全なPathオブジェクトを返す。"""
    target = Path(target_path).resolve()
    root = Path(allowed_root).resolve()

    # is_relative_to() で意味論的なパス比較（str.startswith() より安全）
    try:
        target.relative_to(root)
    except ValueError:
        raise SecurityError(f"書き込み先が許可領域外: {target}")

    if target.is_symlink():
        raise SecurityError(f"シンボリックリンクへの書き込みは禁止: {target}")

    if len(str(target)) > 240:
        raise SecurityError(f"パスが長すぎます（240文字超）: {target}")

    return target


def atomic_write(target_path: Path, content: str) -> None:
    """
    アトミック書き込み。同一ディレクトリへの一時ファイル作成後 os.replace() でリネーム。
    NTFS 同一ボリューム内でアトミックが保証される（%TEMP%は使用しない）。
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=target_path.parent,
        suffix=".tmp",
    )
    tmp_path = Path(tmp_path_str)

    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # 物理書き込み完了を保証してからリネーム

        if target_path.exists():
            mode = os.stat(target_path).st_mode
            if not (mode & stat.S_IWRITE):
                raise PermissionError(
                    f"承認済みファイルへの直接上書きは禁止です: {target_path}\n"
                    f"改訂するには revision_in_progress フローを使用してください。"
                )

        os.replace(tmp_path, str(target_path))

    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def write_with_conflict_check(
    target_path: Path,
    new_content: str,
    expected_revision: int,
    expected_sha256: str,
) -> None:
    """書き込み前に revision と sha256 を確認し、想定外の変更があれば中断する。"""
    if target_path.exists():
        from core.integrity import compute_sha256

        current_revision = _read_revision(target_path)
        if current_revision != expected_revision:
            raise ConflictError(
                f"ファイルが想定外に更新されています "
                f"（期待revision: {expected_revision}, 現在revision: {current_revision}）: {target_path}"
            )

        current_sha256 = compute_sha256(target_path)
        if current_sha256 != expected_sha256:
            raise ConflictError(f"ファイルの内容が変更されています: {target_path}")

    atomic_write(target_path, new_content)


def _read_revision(file_path: Path) -> int:
    """YAMLファイルのトップレベル revision フィールドを読み取る。"""
    from ruamel.yaml import YAML

    yaml = YAML()
    with open(file_path, encoding="utf-8") as f:
        data = yaml.load(f)
    if data and "revision" in data:
        return int(data["revision"])
    return 1


def cleanup_stale_tmp_files(directory: Path, max_age_hours: int = 2) -> list[Path]:
    """
    古い .tmp ファイルを削除する。
    安全条件: ファイル更新時刻が max_age_hours 以上前 かつ 書き込み進行中でない。
    """
    import time

    removed: list[Path] = []
    for tmp_file in directory.rglob("*.tmp"):
        age_hours = (time.time() - tmp_file.stat().st_mtime) / 3600
        if age_hours >= max_age_hours and not _is_write_in_progress(tmp_file):
            tmp_file.unlink(missing_ok=True)
            removed.append(tmp_file)
    return removed


def _is_write_in_progress(tmp_file: Path) -> bool:
    """operation-log を参照して書き込み進行中かチェックする。MVP では常に False を返す。"""
    # TODO: Phase 3 で operation-log 参照を実装する
    return False
