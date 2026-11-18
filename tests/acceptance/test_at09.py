"""
AT-09 受入試験：データ保護テスト
設計仕様: docs/design/07_TEST_PLAN.md AT-09

検証対象：
1. 承認済みプロファイルへの直接上書き → 拒否
2. 許可領域外への書き込み → SecurityError
3. パストラバーサル攻撃 → SecurityError
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from core.approval import approve_museum_profile
from core.models.museum_profile import MuseumProfile
from core.storage import SecurityError, atomic_write, validate_write_path
from core.yaml_io import save_yaml


def _make_approved_profile(museum_dir: Path, museum_id: str) -> Path:
    """テスト用の承認済みプロファイルを作成する。"""
    museum_dir.mkdir(parents=True, exist_ok=True)
    profile = MuseumProfile(museum_id=museum_id, status="ready_for_review")
    profile.basic.name = "架空歴史館（テスト用）"
    draft_path = museum_dir / "museum-profile-draft.yaml"
    save_yaml(draft_path, profile)
    return approve_museum_profile(museum_dir, draft_path, approved_by="テスト承認者")


class TestApprovedFileProtection:
    """AT-09-1: 承認済みファイルへの直接上書き拒否"""

    def test_approved_file_is_readonly(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        versioned_path = _make_approved_profile(museum_dir, "museum-001")
        mode = os.stat(versioned_path).st_mode
        assert not (mode & stat.S_IWRITE), "承認済みファイルは読み取り専用であるべき"

    def test_atomic_write_to_readonly_raises(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        versioned_path = _make_approved_profile(museum_dir, "museum-001")
        with pytest.raises(PermissionError, match="承認済みファイルへの直接上書きは禁止"):
            atomic_write(versioned_path, "改ざんしようとした内容")

    def test_manifest_integrity_preserved(self, tmp_path: Path) -> None:
        from core.integrity import verify_integrity
        from core.models.profile_manifest import ProfileManifest
        from core.yaml_io import load_yaml

        museum_dir = tmp_path / "museum-001"
        versioned_path = _make_approved_profile(museum_dir, "museum-001")
        manifest = load_yaml(museum_dir / "profile-manifest.yaml", ProfileManifest)
        expected_sha256 = manifest.entries[0].sha256
        verify_integrity(versioned_path, expected_sha256)  # 例外なしで通過するはず


class TestPathTraversalProtection:
    """AT-09-2: パストラバーサル攻撃の拒否"""

    def test_traversal_path_rejected(self, tmp_path: Path) -> None:
        allowed_root = str(tmp_path / "data")
        traversal = str(tmp_path / "data" / ".." / ".." / "etc" / "passwd")
        with pytest.raises(SecurityError, match="許可領域外"):
            validate_write_path(traversal, allowed_root)

    def test_sibling_path_rejected(self, tmp_path: Path) -> None:
        allowed_root = str(tmp_path / "museum-001")
        sibling = str(tmp_path / "museum-002" / "secret.yaml")
        with pytest.raises(SecurityError, match="許可領域外"):
            validate_write_path(sibling, allowed_root)

    def test_valid_nested_path_accepted(self, tmp_path: Path) -> None:
        allowed_root = str(tmp_path / "data")
        valid = str(tmp_path / "data" / "museum-001" / "profile.yaml")
        result = validate_write_path(valid, allowed_root)
        assert result.is_relative_to(Path(allowed_root).resolve())


class TestMultiMuseumIsolation:
    """AT-09-3: 複数館のデータが互いに干渉しないこと"""

    def test_two_museums_independent(self, tmp_path: Path) -> None:
        data_root = tmp_path / "data"

        # 2館のプロファイルを個別に承認する
        dir1 = data_root / "museum-001"
        path1 = _make_approved_profile(dir1, "museum-001")

        dir2 = data_root / "museum-002"
        dir2.mkdir(parents=True, exist_ok=True)
        profile2 = MuseumProfile(museum_id="museum-002", status="ready_for_review")
        profile2.basic.name = "架空美術館（テスト用）"
        draft2 = dir2 / "museum-profile-draft.yaml"
        save_yaml(draft2, profile2)
        path2 = approve_museum_profile(dir2, draft2, approved_by="テスト承認者")

        # 両館のマニフェストが独立していることを確認
        from core.models.profile_manifest import ProfileManifest
        from core.yaml_io import load_yaml

        m1 = load_yaml(dir1 / "profile-manifest.yaml", ProfileManifest)
        m2 = load_yaml(dir2 / "profile-manifest.yaml", ProfileManifest)
        assert m1.museum_id == "museum-001"
        assert m2.museum_id == "museum-002"
        assert m1.entries[0].sha256 != m2.entries[0].sha256

    def test_museum1_approval_does_not_affect_museum2(self, tmp_path: Path) -> None:
        data_root = tmp_path / "data"

        # museum-001 を承認
        dir1 = data_root / "museum-001"
        _make_approved_profile(dir1, "museum-001")

        # museum-002 はドラフトのまま
        dir2 = data_root / "museum-002"
        dir2.mkdir(parents=True, exist_ok=True)
        assert not (dir2 / "museum-profile-v1.yaml").exists()
        assert not (dir2 / "profile-manifest.yaml").exists()
