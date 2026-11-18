"""core/storage.py の単体テスト"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

# プロジェクトルートを sys.path に追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.storage import (
    SecurityError,
    ConflictError,
    atomic_write,
    validate_write_path,
    write_with_conflict_check,
    cleanup_stale_tmp_files,
)


# ──────────────────────────────────────────────
# validate_write_path
# ──────────────────────────────────────────────

class TestValidateWritePath:
    def test_valid_path_inside_root(self, tmp_path):
        result = validate_write_path(str(tmp_path / "file.yaml"), str(tmp_path))
        assert result == (tmp_path / "file.yaml").resolve()

    def test_valid_nested_path(self, tmp_path):
        nested = tmp_path / "museums" / "museum-001" / "profile.yaml"
        result = validate_write_path(str(nested), str(tmp_path))
        assert result == nested.resolve()

    def test_path_traversal_rejected(self, tmp_path):
        with pytest.raises(SecurityError, match="許可領域外"):
            validate_write_path(str(tmp_path / ".." / "escape.yaml"), str(tmp_path))

    def test_outside_root_rejected(self, tmp_path):
        with pytest.raises(SecurityError, match="許可領域外"):
            validate_write_path("C:/Windows/System32/evil.yaml", str(tmp_path))

    def test_path_too_long_rejected(self, tmp_path):
        long_name = "a" * 220
        with pytest.raises(SecurityError, match="長すぎます"):
            validate_write_path(str(tmp_path / long_name / "file.yaml"), str(tmp_path))


# ──────────────────────────────────────────────
# atomic_write
# ──────────────────────────────────────────────

class TestAtomicWrite:
    def test_new_file_created(self, tmp_path):
        target = tmp_path / "output.yaml"
        atomic_write(target, "schema_version: '1.0'\n")
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "schema_version: '1.0'\n"

    def test_existing_file_overwritten(self, tmp_path):
        target = tmp_path / "output.yaml"
        target.write_text("old content", encoding="utf-8")
        atomic_write(target, "new content")
        assert target.read_text(encoding="utf-8") == "new content"

    def test_nested_dir_created(self, tmp_path):
        target = tmp_path / "a" / "b" / "c" / "file.yaml"
        atomic_write(target, "content")
        assert target.exists()

    def test_no_tmp_file_left_on_success(self, tmp_path):
        target = tmp_path / "output.yaml"
        atomic_write(target, "content")
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_readonly_file_raises_permission_error(self, tmp_path):
        target = tmp_path / "approved.yaml"
        target.write_text("approved content", encoding="utf-8")
        # 読み取り専用に設定
        current = os.stat(target).st_mode
        os.chmod(target, current & ~stat.S_IWRITE)

        try:
            with pytest.raises(PermissionError, match="承認済みファイル"):
                atomic_write(target, "new content")
        finally:
            # クリーンアップ: 書き込み権限を戻す
            os.chmod(target, current | stat.S_IWRITE)

    def test_no_tmp_file_left_on_readonly_error(self, tmp_path):
        target = tmp_path / "approved.yaml"
        target.write_text("approved content", encoding="utf-8")
        current = os.stat(target).st_mode
        os.chmod(target, current & ~stat.S_IWRITE)

        try:
            with pytest.raises(PermissionError):
                atomic_write(target, "new content")
            tmp_files = list(tmp_path.glob("*.tmp"))
            assert tmp_files == []
        finally:
            os.chmod(target, current | stat.S_IWRITE)


# ──────────────────────────────────────────────
# write_with_conflict_check
# ──────────────────────────────────────────────

class TestWriteWithConflictCheck:
    def _make_yaml(self, tmp_path: Path, revision: int, content: str) -> Path:
        from io import StringIO
        from ruamel.yaml import YAML
        target = tmp_path / "artifact.yaml"
        yaml = YAML()
        stream = StringIO()
        yaml.dump({"revision": revision, "content": content}, stream)
        target.write_text(stream.getvalue(), encoding="utf-8")
        return target

    def test_new_file_no_check(self, tmp_path):
        target = tmp_path / "new.yaml"
        write_with_conflict_check(target, "content", expected_revision=1, expected_sha256="")
        assert target.exists()

    def test_matching_revision_and_hash(self, tmp_path):
        import hashlib
        target = self._make_yaml(tmp_path, revision=1, content="hello")
        expected_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
        write_with_conflict_check(
            target, "new content", expected_revision=1, expected_sha256=expected_sha256
        )
        assert target.read_text(encoding="utf-8") == "new content"

    def test_revision_mismatch_raises(self, tmp_path):
        target = self._make_yaml(tmp_path, revision=2, content="hello")
        from core.integrity import compute_sha256
        sha = compute_sha256(target)
        with pytest.raises(ConflictError, match="想定外に更新"):
            write_with_conflict_check(target, "x", expected_revision=1, expected_sha256=sha)

    def test_hash_mismatch_raises(self, tmp_path):
        target = self._make_yaml(tmp_path, revision=1, content="hello")
        with pytest.raises(ConflictError, match="内容が変更"):
            write_with_conflict_check(
                target, "x", expected_revision=1, expected_sha256="0" * 64
            )


# ──────────────────────────────────────────────
# cleanup_stale_tmp_files
# ──────────────────────────────────────────────

class TestCleanupStaleTmpFiles:
    def test_fresh_tmp_not_deleted(self, tmp_path):
        tmp_file = tmp_path / "file.tmp"
        tmp_file.write_text("temp", encoding="utf-8")
        removed = cleanup_stale_tmp_files(tmp_path, max_age_hours=2)
        assert tmp_file.exists()
        assert removed == []

    def test_old_tmp_deleted(self, tmp_path):
        import time
        tmp_file = tmp_path / "old.tmp"
        tmp_file.write_text("temp", encoding="utf-8")
        # mtime を 3 時間前に設定
        old_mtime = time.time() - 3 * 3600
        os.utime(tmp_file, (old_mtime, old_mtime))
        removed = cleanup_stale_tmp_files(tmp_path, max_age_hours=2)
        assert not tmp_file.exists()
        assert tmp_file in removed
