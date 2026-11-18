"""core.yaml_io の単体テスト"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.models.museum_profile import MuseumProfile
from core.models.profile_manifest import ProfileManifest
from core.yaml_io import load_yaml, load_yaml_raw, save_yaml


class TestLoadYaml:
    def test_load_valid_model(self, tmp_path: Path) -> None:
        f = tmp_path / "profile.yaml"
        f.write_text(
            "museum_id: test-001\nschema_version: '1.0'\n",
            encoding="utf-8",
        )
        profile = load_yaml(f, MuseumProfile)
        assert profile.museum_id == "test-001"

    def test_extra_fields_are_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / "profile.yaml"
        f.write_text(
            "museum_id: test-002\nunknown_field: xyz\n",
            encoding="utf-8",
        )
        profile = load_yaml(f, MuseumProfile)
        assert profile.museum_id == "test-002"

    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.yaml"
        f.write_text("{}\n", encoding="utf-8")
        # museum_id は必須なのでバリデーションエラーになる
        with pytest.raises(Exception):
            load_yaml(f, MuseumProfile)


class TestSaveYaml:
    def test_save_and_reload(self, tmp_path: Path) -> None:
        profile = MuseumProfile(museum_id="museum-001")
        profile.basic.name = "テスト歴史館"
        f = tmp_path / "profile.yaml"
        save_yaml(f, profile)
        reloaded = load_yaml(f, MuseumProfile)
        assert reloaded.museum_id == "museum-001"
        assert reloaded.basic.name == "テスト歴史館"

    def test_save_manifest(self, tmp_path: Path) -> None:
        from core.models.profile_manifest import ProfileEntry
        manifest = ProfileManifest(museum_id="museum-001")
        manifest.entries.append(
            ProfileEntry(
                version=1,
                filename="museum-profile-v1.yaml",
                sha256="abc123",
                approved_at="2026-01-01T00:00:00+00:00",
            )
        )
        f = tmp_path / "manifest.yaml"
        save_yaml(f, manifest)
        reloaded = load_yaml(f, ProfileManifest)
        assert len(reloaded.entries) == 1
        assert reloaded.entries[0].sha256 == "abc123"

    def test_nested_dir_created(self, tmp_path: Path) -> None:
        profile = MuseumProfile(museum_id="museum-001")
        f = tmp_path / "sub" / "dir" / "profile.yaml"
        save_yaml(f, profile)
        assert f.exists()


class TestLoadYamlRaw:
    def test_load_raw_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "data.yaml"
        f.write_text("key: value\nlist:\n  - a\n  - b\n", encoding="utf-8")
        data = load_yaml_raw(f)
        assert data["key"] == "value"
        assert data["list"] == ["a", "b"]

    def test_empty_file_returns_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.yaml"
        f.write_text("{}\n", encoding="utf-8")
        data = load_yaml_raw(f)
        assert isinstance(data, dict)
