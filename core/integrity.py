"""
ハッシュ整合性検証・承認済みファイル保護
設計仕様: docs/design/05_STORAGE_SECURITY_DESIGN.md §4
"""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path


class IntegrityError(Exception):
    pass


def compute_sha256(file_path: Path) -> str:
    """ファイルの SHA-256 ハッシュ（hex）を計算する。"""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify_integrity(file_path: Path, expected_sha256: str) -> bool:
    """
    ファイルの SHA-256 ハッシュが期待値と一致するか検証する。
    不一致の場合は IntegrityError を送出する（自動修復はしない）。
    """
    actual = compute_sha256(file_path)
    if actual != expected_sha256:
        raise IntegrityError(
            f"ファイルの整合性チェック失敗: {file_path}\n"
            f"  期待値: {expected_sha256}\n"
            f"  実際値: {actual}\n"
            f"  このファイルは承認後に変更された可能性があります。"
        )
    return True


def protect_approved_file(file_path: Path) -> None:
    """承認済みファイルを読み取り専用属性に設定する（誤操作抑止・第3層保護）。"""
    current = os.stat(file_path).st_mode
    os.chmod(file_path, current & ~stat.S_IWRITE)


def unprotect_for_revision(file_path: Path) -> None:
    """改訂フロー開始時に読み取り専用属性を解除する。ハッシュ検証（第2層）は維持される。"""
    current = os.stat(file_path).st_mode
    os.chmod(file_path, current | stat.S_IWRITE)
