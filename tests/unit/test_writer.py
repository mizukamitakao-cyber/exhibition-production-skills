"""core/writer.py のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.models.artifact_manifest import ArtifactManifest
from core.planner import create_artifact_manifest, save_artifact_manifest
from core.writer import (
    WriterError,
    check_prerequisite_approved,
    create_revision_manuscript,
    get_latest_manuscript_version,
    get_manuscripts_dir,
    list_manuscripts,
    load_manuscript,
    register_manuscript_artifact,
    save_manuscript,
)


def test_save_manuscript(tmp_path):
    content = "# パネル01\n\n本文テキスト"
    path = save_manuscript(tmp_path, "panel-01", content, version=1)
    assert path.exists()
    assert path.name == "panel-01-v1.md"
    assert path.read_text(encoding="utf-8") == content


def test_load_manuscript(tmp_path):
    save_manuscript(tmp_path, "panel-01", "# パネル01", version=1)
    result = load_manuscript(tmp_path, "panel-01", version=1)
    assert result is not None
    assert "パネル01" in result


def test_load_manuscript_missing_returns_none(tmp_path):
    result = load_manuscript(tmp_path, "panel-99", version=1)
    assert result is None


def test_get_latest_manuscript_version_no_files(tmp_path):
    result = get_latest_manuscript_version(tmp_path, "panel-01")
    assert result == 0


def test_get_latest_manuscript_version_single(tmp_path):
    save_manuscript(tmp_path, "panel-01", "v1", version=1)
    assert get_latest_manuscript_version(tmp_path, "panel-01") == 1


def test_get_latest_manuscript_version_multiple(tmp_path):
    for v in (1, 2, 3):
        save_manuscript(tmp_path, "panel-01", f"v{v}", version=v)
    assert get_latest_manuscript_version(tmp_path, "panel-01") == 3


def test_get_latest_manuscript_version_panel_independent(tmp_path):
    save_manuscript(tmp_path, "panel-01", "p01 v1", version=1)
    save_manuscript(tmp_path, "panel-02", "p02 v1", version=1)
    save_manuscript(tmp_path, "panel-02", "p02 v2", version=2)
    assert get_latest_manuscript_version(tmp_path, "panel-01") == 1
    assert get_latest_manuscript_version(tmp_path, "panel-02") == 2


def test_list_manuscripts(tmp_path):
    save_manuscript(tmp_path, "panel-01", "v1", version=1)
    save_manuscript(tmp_path, "panel-02", "v1", version=1)
    result = list_manuscripts(tmp_path)
    assert len(result) == 2
    ids = {m["panel_id"] for m in result}
    assert "panel-01" in ids
    assert "panel-02" in ids


def test_list_manuscripts_empty(tmp_path):
    result = list_manuscripts(tmp_path)
    assert result == []


def test_create_revision_manuscript(tmp_path):
    save_manuscript(tmp_path, "panel-01", "# 原本\n\n本文", version=1)
    new_version, original = create_revision_manuscript(tmp_path, "panel-01")
    assert new_version == 2
    assert "原本" in original


def test_create_revision_uses_specified_version(tmp_path):
    for v in (1, 2):
        save_manuscript(tmp_path, "panel-01", f"v{v}", version=v)
    new_version, original = create_revision_manuscript(tmp_path, "panel-01", current_version=1)
    assert new_version == 2
    assert original == "v1"


def test_create_revision_nonexistent_raises(tmp_path):
    with pytest.raises(WriterError, match="存在しません"):
        create_revision_manuscript(tmp_path, "no-such-panel")


def test_create_revision_does_not_overwrite_original(tmp_path):
    save_manuscript(tmp_path, "panel-01", "# 原本", version=1)
    new_version, _ = create_revision_manuscript(tmp_path, "panel-01")
    # 新バージョンを保存しても旧バージョンは保持
    save_manuscript(tmp_path, "panel-01", "# 改訂版", version=new_version)
    original = load_manuscript(tmp_path, "panel-01", version=1)
    assert original == "# 原本"


def test_register_manuscript_artifact(tmp_path):
    save_manuscript(tmp_path, "panel-01", "v1", version=1)
    manifest = create_artifact_manifest("proj-01")
    artifact = register_manuscript_artifact(manifest, tmp_path, "panel-01", version=1, title="パネル01")
    assert artifact.artifact_id == "panel-01-v1"
    assert artifact.type == "manuscript"
    assert len(manifest.artifacts) == 1


def test_register_manuscript_updates_existing(tmp_path):
    save_manuscript(tmp_path, "panel-01", "v1", version=1)
    manifest = create_artifact_manifest("proj-01")
    register_manuscript_artifact(manifest, tmp_path, "panel-01", version=1)
    register_manuscript_artifact(manifest, tmp_path, "panel-01", version=1)
    assert len(manifest.artifacts) == 1


def test_check_prerequisite_approved_true(tmp_path):
    manifest = create_artifact_manifest("proj-01")
    from core.planner import add_artifact
    from core.models.artifact_manifest import Artifact
    a = Artifact(artifact_id="story-v1", type="story-structure",
                 title="構成表", version=1, status="approved")
    add_artifact(manifest, a)
    assert check_prerequisite_approved(manifest, "story-v1") is True


def test_check_prerequisite_approved_false_draft(tmp_path):
    manifest = create_artifact_manifest("proj-01")
    from core.planner import add_artifact
    from core.models.artifact_manifest import Artifact
    a = Artifact(artifact_id="story-v1", type="story-structure",
                 title="構成表", version=1, status="draft")
    add_artifact(manifest, a)
    assert check_prerequisite_approved(manifest, "story-v1") is False


def test_check_prerequisite_approved_false_missing():
    manifest = create_artifact_manifest("proj-01")
    assert check_prerequisite_approved(manifest, "no-such") is False
