"""core/planner.py のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.models.artifact_manifest import Artifact
from core.planner import (
    PlannerError,
    add_artifact,
    create_artifact_manifest,
    get_artifact,
    get_latest_plan_version,
    load_artifact_manifest,
    load_plan_draft,
    register_plan_artifact,
    save_artifact_manifest,
    save_plan_draft,
    update_artifact_status,
)


def _make_artifact(artifact_id: str, type_: str = "plan") -> Artifact:
    return Artifact(
        artifact_id=artifact_id,
        type=type_,
        title="テスト成果物",
        version=1,
    )


def test_create_artifact_manifest():
    manifest = create_artifact_manifest("proj-01")
    assert manifest.project_id == "proj-01"
    assert manifest.artifacts == []


def test_add_artifact():
    manifest = create_artifact_manifest("proj-01")
    add_artifact(manifest, _make_artifact("plan-v1"))
    assert len(manifest.artifacts) == 1


def test_add_artifact_duplicate_raises():
    manifest = create_artifact_manifest("proj-01")
    add_artifact(manifest, _make_artifact("plan-v1"))
    with pytest.raises(PlannerError, match="重複"):
        add_artifact(manifest, _make_artifact("plan-v1"))


def test_get_artifact_found():
    manifest = create_artifact_manifest("proj-01")
    add_artifact(manifest, _make_artifact("plan-v1"))
    result = get_artifact(manifest, "plan-v1")
    assert result is not None
    assert result.artifact_id == "plan-v1"


def test_get_artifact_not_found():
    manifest = create_artifact_manifest("proj-01")
    result = get_artifact(manifest, "no-such")
    assert result is None


def test_update_artifact_status_to_approved():
    manifest = create_artifact_manifest("proj-01")
    add_artifact(manifest, _make_artifact("plan-v1"))
    update_artifact_status(manifest, "plan-v1", "approved")
    artifact = get_artifact(manifest, "plan-v1")
    assert artifact is not None
    assert artifact.status == "approved"
    assert artifact.approved_at is not None


def test_update_artifact_status_to_draft():
    manifest = create_artifact_manifest("proj-01")
    add_artifact(manifest, _make_artifact("plan-v1"))
    update_artifact_status(manifest, "plan-v1", "ready_for_review")
    artifact = get_artifact(manifest, "plan-v1")
    assert artifact is not None
    assert artifact.status == "ready_for_review"


def test_update_artifact_status_not_found_raises():
    manifest = create_artifact_manifest("proj-01")
    with pytest.raises(PlannerError, match="見つかりません"):
        update_artifact_status(manifest, "no-such", "approved")


def test_save_plan_draft(tmp_path):
    content = "# 企画書 v1\n\n本文"
    path = save_plan_draft(tmp_path, content, version=1)
    assert path.exists()
    assert path.name == "exhibition-plan-v1.md"
    assert path.read_text(encoding="utf-8") == content


def test_load_plan_draft(tmp_path):
    save_plan_draft(tmp_path, "# 企画書 v1", version=1)
    result = load_plan_draft(tmp_path, version=1)
    assert result is not None
    assert "企画書 v1" in result


def test_load_plan_draft_missing_returns_none(tmp_path):
    result = load_plan_draft(tmp_path, version=99)
    assert result is None


def test_get_latest_plan_version_no_plans(tmp_path):
    result = get_latest_plan_version(tmp_path)
    assert result == 0


def test_get_latest_plan_version_single(tmp_path):
    save_plan_draft(tmp_path, "v1 content", version=1)
    result = get_latest_plan_version(tmp_path)
    assert result == 1


def test_get_latest_plan_version_multiple(tmp_path):
    for v in (1, 2, 3):
        save_plan_draft(tmp_path, f"v{v} content", version=v)
    result = get_latest_plan_version(tmp_path)
    assert result == 3


def test_register_plan_artifact(tmp_path):
    manifest = create_artifact_manifest("proj-01")
    save_plan_draft(tmp_path, "# 企画書 v1", version=1)
    artifact = register_plan_artifact(manifest, tmp_path, version=1, title="テスト企画書")
    assert artifact.artifact_id == "plan-v1"
    assert artifact.type == "plan"
    assert artifact.version == 1
    assert len(manifest.artifacts) == 1


def test_save_and_load_manifest(tmp_path):
    manifest = create_artifact_manifest("proj-io")
    add_artifact(manifest, _make_artifact("plan-v1"))
    save_artifact_manifest(manifest, tmp_path)
    loaded = load_artifact_manifest(tmp_path)
    assert loaded is not None
    assert loaded.project_id == "proj-io"
    assert len(loaded.artifacts) == 1


def test_load_manifest_missing_returns_none(tmp_path):
    result = load_artifact_manifest(tmp_path)
    assert result is None
