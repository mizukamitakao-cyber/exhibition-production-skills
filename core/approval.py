"""
承認・保護ロジック（多層保護）。
設計仕様: docs/design/05_STORAGE_SECURITY_DESIGN.md §4
  第1層: 版管理ファイル名（museum-profile-vN.yaml）
  第2層: SHA-256ハッシュをprofile-manifest.yamlに記録
  第3層: ファイル属性を読み取り専用に設定
  第4層: 監査ログ（operation-log.yaml）
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from core.integrity import compute_sha256, protect_approved_file
from core.models.museum_profile import MuseumProfile
from core.models.profile_manifest import ProfileManifest, ProfileEntry
from core.yaml_io import load_yaml, save_yaml


class ApprovalError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def approve_museum_profile(
    museum_dir: Path,
    draft_path: Path,
    approved_by: str | None = None,
) -> Path:
    """
    museum-profile-draft.yaml を承認し、versioned なファイルへ確定する。

    Returns: 承認済みプロファイルのパス（museum-profile-vN.yaml）
    """
    if not draft_path.exists():
        raise ApprovalError(f"ドラフトが見つかりません: {draft_path}")

    profile = load_yaml(draft_path, MuseumProfile)
    if profile.status not in ("draft", "ready_for_review", "revision_in_progress"):
        raise ApprovalError(f"承認可能な状態ではありません: {profile.status}")

    manifest_path = museum_dir / "profile-manifest.yaml"
    if manifest_path.exists():
        manifest = load_yaml(manifest_path, ProfileManifest)
        next_version = max((e.version for e in manifest.entries), default=0) + 1
    else:
        manifest = ProfileManifest(museum_id=profile.museum_id)
        next_version = 1

    now = _now_iso()
    profile.status = "approved"
    profile.profile_version = next_version
    profile.approved_at = now
    profile.approved_by = approved_by
    profile.updated_at = now

    versioned_path = museum_dir / f"museum-profile-v{next_version}.yaml"
    save_yaml(versioned_path, profile)

    sha256 = compute_sha256(versioned_path)
    manifest.entries.append(
        ProfileEntry(
            version=next_version,
            filename=versioned_path.name,
            sha256=sha256,
            approved_at=now,
            approved_by=approved_by,
        )
    )
    save_yaml(manifest_path, manifest)

    protect_approved_file(versioned_path)

    backup_dir = museum_dir / "_backup"
    backup_dir.mkdir(exist_ok=True)
    shutil.move(
        str(draft_path),
        str(backup_dir / f"museum-profile-draft-pre-v{next_version}.yaml"),
    )

    return versioned_path


def begin_revision(
    museum_dir: Path,
    version: int,
    reason: str = "",
) -> Path:
    """
    承認済みプロファイルの改訂を開始する。
    承認済みファイルからドラフトを作成し、status を revision_in_progress に変更する。

    Returns: 新しいドラフトパス
    """
    versioned_path = museum_dir / f"museum-profile-v{version}.yaml"
    if not versioned_path.exists():
        raise ApprovalError(f"承認済みプロファイルが見つかりません: {versioned_path}")

    profile = load_yaml(versioned_path, MuseumProfile)
    if profile.status != "approved":
        raise ApprovalError(f"承認済み状態ではありません: {profile.status}")

    now = _now_iso()
    profile.status = "revision_in_progress"
    profile.updated_at = now

    draft_path = museum_dir / "museum-profile-draft.yaml"
    save_yaml(draft_path, profile)

    return draft_path


def get_latest_approved_version(museum_dir: Path) -> int | None:
    """最新の承認済みバージョン番号を返す。なければ None。"""
    manifest_path = museum_dir / "profile-manifest.yaml"
    if not manifest_path.exists():
        return None
    manifest = load_yaml(manifest_path, ProfileManifest)
    if not manifest.entries:
        return None
    return max(e.version for e in manifest.entries)
