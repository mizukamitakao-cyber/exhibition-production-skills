"""core.approval の単体テスト"""
from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from core.approval import ApprovalError, approve_museum_profile, begin_revision, get_latest_approved_version
from core.models.museum_profile import MuseumProfile
from core.models.profile_manifest import ProfileManifest
from core.yaml_io import load_yaml, save_yaml


def _make_draft(museum_dir: Path, museum_id: str) -> Path:
    museum_dir.mkdir(parents=True, exist_ok=True)
    profile = MuseumProfile(museum_id=museum_id, status="ready_for_review")
    profile.basic.name = "架空歴史館"
    draft_path = museum_dir / "museum-profile-draft.yaml"
    save_yaml(draft_path, profile)
    return draft_path


class TestApproveMesuumProfile:
    def test_creates_versioned_file(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        draft_path = _make_draft(museum_dir, "museum-001")
        versioned = approve_museum_profile(museum_dir, draft_path, approved_by="学芸員A")
        assert versioned.name == "museum-profile-v1.yaml"
        assert versioned.exists()

    def test_versioned_file_is_readonly(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        draft_path = _make_draft(museum_dir, "museum-001")
        versioned = approve_museum_profile(museum_dir, draft_path)
        mode = os.stat(versioned).st_mode
        assert not (mode & stat.S_IWRITE)

    def test_manifest_records_sha256(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        draft_path = _make_draft(museum_dir, "museum-001")
        approve_museum_profile(museum_dir, draft_path, approved_by="学芸員A")
        manifest = load_yaml(museum_dir / "profile-manifest.yaml", ProfileManifest)
        assert len(manifest.entries) == 1
        assert len(manifest.entries[0].sha256) == 64
        assert manifest.entries[0].approved_by == "学芸員A"

    def test_second_approval_creates_v2(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        draft_path = _make_draft(museum_dir, "museum-001")
        v1 = approve_museum_profile(museum_dir, draft_path)

        # 再ドラフト作成
        draft_path2 = _make_draft(museum_dir, "museum-001")
        v2 = approve_museum_profile(museum_dir, draft_path2)
        assert v2.name == "museum-profile-v2.yaml"

    def test_draft_moved_to_backup(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        draft_path = _make_draft(museum_dir, "museum-001")
        approve_museum_profile(museum_dir, draft_path)
        assert not draft_path.exists()
        backup_files = list((museum_dir / "_backup").iterdir())
        assert len(backup_files) == 1

    def test_nonexistent_draft_raises(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        museum_dir.mkdir()
        with pytest.raises(ApprovalError, match="見つかりません"):
            approve_museum_profile(museum_dir, museum_dir / "museum-profile-draft.yaml")

    def test_already_approved_raises(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        museum_dir.mkdir()
        profile = MuseumProfile(museum_id="museum-001", status="approved")
        draft_path = museum_dir / "museum-profile-draft.yaml"
        save_yaml(draft_path, profile)
        with pytest.raises(ApprovalError, match="承認可能な状態ではありません"):
            approve_museum_profile(museum_dir, draft_path)


class TestBeginRevision:
    def test_creates_draft_from_approved(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        draft_path = _make_draft(museum_dir, "museum-001")
        approve_museum_profile(museum_dir, draft_path)

        revision_draft = begin_revision(museum_dir, version=1)
        assert revision_draft.exists()
        profile = load_yaml(revision_draft, MuseumProfile)
        assert profile.status == "revision_in_progress"

    def test_nonexistent_version_raises(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        museum_dir.mkdir()
        with pytest.raises(ApprovalError, match="見つかりません"):
            begin_revision(museum_dir, version=99)

    def test_non_approved_raises(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        museum_dir.mkdir()
        profile = MuseumProfile(museum_id="museum-001", status="draft")
        v1_path = museum_dir / "museum-profile-v1.yaml"
        save_yaml(v1_path, profile)
        with pytest.raises(ApprovalError, match="承認済み状態ではありません"):
            begin_revision(museum_dir, version=1)


class TestGetLatestApprovedVersion:
    def test_returns_none_when_no_manifest(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        museum_dir.mkdir()
        assert get_latest_approved_version(museum_dir) is None

    def test_returns_max_version(self, tmp_path: Path) -> None:
        museum_dir = tmp_path / "museum-001"
        draft_path = _make_draft(museum_dir, "museum-001")
        approve_museum_profile(museum_dir, draft_path)
        draft_path2 = _make_draft(museum_dir, "museum-001")
        approve_museum_profile(museum_dir, draft_path2)
        assert get_latest_approved_version(museum_dir) == 2
