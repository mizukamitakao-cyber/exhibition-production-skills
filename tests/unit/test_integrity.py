"""core/integrity.py の単体テスト"""
from __future__ import annotations

import hashlib
import os
import stat
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.integrity import (
    IntegrityError,
    compute_sha256,
    verify_integrity,
    protect_approved_file,
    unprotect_for_revision,
)


class TestComputeSha256:
    def test_known_hash(self, tmp_path):
        target = tmp_path / "file.txt"
        target.write_bytes(b"hello")
        expected = hashlib.sha256(b"hello").hexdigest()
        assert compute_sha256(target) == expected

    def test_empty_file(self, tmp_path):
        target = tmp_path / "empty.txt"
        target.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert compute_sha256(target) == expected

    def test_different_content_different_hash(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"content a")
        b.write_bytes(b"content b")
        assert compute_sha256(a) != compute_sha256(b)


class TestVerifyIntegrity:
    def test_matching_hash_returns_true(self, tmp_path):
        target = tmp_path / "file.yaml"
        target.write_bytes(b"schema_version: '1.0'\n")
        sha = compute_sha256(target)
        assert verify_integrity(target, sha) is True

    def test_hash_mismatch_raises_integrity_error(self, tmp_path):
        target = tmp_path / "file.yaml"
        target.write_bytes(b"original content")
        with pytest.raises(IntegrityError, match="整合性チェック失敗"):
            verify_integrity(target, "0" * 64)

    def test_error_message_contains_file_path(self, tmp_path):
        target = tmp_path / "museum-profile-v1.yaml"
        target.write_bytes(b"content")
        with pytest.raises(IntegrityError) as exc_info:
            verify_integrity(target, "badhash")
        assert "museum-profile-v1.yaml" in str(exc_info.value)


class TestProtectApprovedFile:
    def test_file_becomes_readonly(self, tmp_path):
        target = tmp_path / "approved.yaml"
        target.write_text("approved", encoding="utf-8")
        protect_approved_file(target)
        mode = os.stat(target).st_mode
        try:
            assert not (mode & stat.S_IWRITE)
        finally:
            unprotect_for_revision(target)

    def test_unprotect_restores_writability(self, tmp_path):
        target = tmp_path / "approved.yaml"
        target.write_text("approved", encoding="utf-8")
        protect_approved_file(target)
        unprotect_for_revision(target)
        mode = os.stat(target).st_mode
        assert mode & stat.S_IWRITE
