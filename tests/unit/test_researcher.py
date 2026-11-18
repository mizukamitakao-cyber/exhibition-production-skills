"""core/researcher.py のユニットテスト。"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.models.source_registry import Source
from core.researcher import (
    ResearchError,
    add_source,
    create_source_registry,
    get_unverified_sources,
    load_registry,
    load_research_memo,
    mark_unverified,
    mark_verified,
    record_usage,
    save_registry,
    save_research_memo,
    update_source,
)


def _make_source(source_id: str, title: str = "テスト出典") -> Source:
    return Source(
        source_id=source_id,
        type="academic",
        title=title,
        verification_status="unverified",
    )


def test_create_source_registry():
    reg = create_source_registry("proj-01")
    assert reg.project_id == "proj-01"
    assert reg.sources == []
    assert reg.source_usage == []


def test_add_source():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))
    assert len(reg.sources) == 1
    assert reg.sources[0].source_id == "src-001"


def test_add_source_duplicate_raises():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))
    with pytest.raises(ResearchError, match="重複"):
        add_source(reg, _make_source("src-001"))


def test_add_source_updates_updated_at():
    reg = create_source_registry("proj-01")
    old_ts = reg.updated_at
    import time; time.sleep(0.01)
    add_source(reg, _make_source("src-001"))
    assert reg.updated_at >= old_ts


def test_update_source():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))
    update_source(reg, "src-001", title="更新後タイトル")
    assert reg.sources[0].title == "更新後タイトル"


def test_update_source_not_found_raises():
    reg = create_source_registry("proj-01")
    with pytest.raises(ResearchError, match="見つかりません"):
        update_source(reg, "no-such-source", title="x")


def test_mark_verified():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))
    mark_verified(reg, "src-001")
    assert reg.sources[0].verification_status == "verified"


def test_mark_unverified():
    reg = create_source_registry("proj-01")
    src = _make_source("src-001")
    src.verification_status = "verified"
    add_source(reg, src)
    mark_unverified(reg, "src-001")
    assert reg.sources[0].verification_status == "unverified"


def test_get_unverified_sources_empty():
    reg = create_source_registry("proj-01")
    src = _make_source("src-001")
    src.verification_status = "verified"
    add_source(reg, src)
    result = get_unverified_sources(reg)
    assert result == []


def test_get_unverified_sources_returns_unverified():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))  # verification_status = "unverified"
    src2 = _make_source("src-002")
    src2.verification_status = "verified"
    add_source(reg, src2)
    result = get_unverified_sources(reg)
    assert len(result) == 1
    assert result[0].source_id == "src-001"


def test_get_unverified_sources_includes_empty_status():
    reg = create_source_registry("proj-01")
    src = _make_source("src-001")
    src.verification_status = ""
    add_source(reg, src)
    result = get_unverified_sources(reg)
    assert len(result) == 1


def test_record_usage_new():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))
    record_usage(reg, "src-001", "plan-v1", "第1章")
    assert len(reg.source_usage) == 1
    usage = reg.source_usage[0]
    assert usage.source_id == "src-001"
    assert "plan-v1" in usage.used_in_artifacts
    assert usage.sections == "第1章"


def test_record_usage_appends_artifact():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))
    record_usage(reg, "src-001", "plan-v1")
    record_usage(reg, "src-001", "story-v1")
    usage = reg.source_usage[0]
    assert "plan-v1" in usage.used_in_artifacts
    assert "story-v1" in usage.used_in_artifacts


def test_record_usage_no_duplicate_artifact():
    reg = create_source_registry("proj-01")
    add_source(reg, _make_source("src-001"))
    record_usage(reg, "src-001", "plan-v1")
    record_usage(reg, "src-001", "plan-v1")
    assert reg.source_usage[0].used_in_artifacts.count("plan-v1") == 1


def test_save_and_load_registry(tmp_path):
    reg = create_source_registry("proj-io")
    add_source(reg, _make_source("src-001", "保存テスト出典"))
    save_registry(reg, tmp_path)
    loaded = load_registry(tmp_path)
    assert loaded is not None
    assert loaded.project_id == "proj-io"
    assert len(loaded.sources) == 1
    assert loaded.sources[0].title == "保存テスト出典"


def test_load_registry_missing_returns_none(tmp_path):
    result = load_registry(tmp_path)
    assert result is None


def test_save_research_memo(tmp_path):
    path = save_research_memo(tmp_path, "001", "# テスト調査メモ\n\nコンテンツ")
    assert path.exists()
    assert path.name == "memo-001.md"
    content = path.read_text(encoding="utf-8")
    assert "テスト調査メモ" in content


def test_load_research_memo(tmp_path):
    save_research_memo(tmp_path, "001", "# メモ")
    result = load_research_memo(tmp_path, "001")
    assert result is not None
    assert "# メモ" in result


def test_load_research_memo_missing_returns_none(tmp_path):
    result = load_research_memo(tmp_path, "999")
    assert result is None
