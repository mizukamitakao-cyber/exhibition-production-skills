"""
原稿管理。
Exhibition Writer スキルのPythonサポート。

改訂モード原則：
- 原本（既存原稿）は上書きしない
- 改訂版を新しいバージョン番号で保存する
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.models.artifact_manifest import Artifact, ArtifactManifest
from core.storage import atomic_write
from core.yaml_io import load_yaml, save_yaml


class WriterError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_manuscripts_dir(project_dir: Path) -> Path:
    return project_dir / "manuscripts"


def _manuscript_filename(panel_id: str, version: int) -> str:
    return f"{panel_id}-v{version}.md"


def save_manuscript(
    project_dir: Path,
    panel_id: str,
    content: str,
    version: int = 1,
) -> Path:
    """原稿をアトミックに保存する。"""
    ms_dir = get_manuscripts_dir(project_dir)
    ms_dir.mkdir(exist_ok=True)
    path = ms_dir / _manuscript_filename(panel_id, version)
    atomic_write(path, content)
    return path


def load_manuscript(project_dir: Path, panel_id: str, version: int) -> str | None:
    path = get_manuscripts_dir(project_dir) / _manuscript_filename(panel_id, version)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def get_latest_manuscript_version(project_dir: Path, panel_id: str) -> int:
    """panel_id の最新バージョン番号を返す。存在しない場合は 0。"""
    ms_dir = get_manuscripts_dir(project_dir)
    if not ms_dir.exists():
        return 0
    best = 0
    for f in ms_dir.glob(f"{panel_id}-v*.md"):
        try:
            v = int(f.stem.split("-v")[1])
            if v > best:
                best = v
        except (IndexError, ValueError):
            pass
    return best


def list_manuscripts(project_dir: Path) -> list[dict]:
    """manuscripts/ 内のすべての原稿情報を返す。"""
    ms_dir = get_manuscripts_dir(project_dir)
    if not ms_dir.exists():
        return []
    result = []
    for f in sorted(ms_dir.glob("*.md")):
        parts = f.stem.rsplit("-v", 1)
        if len(parts) == 2:
            try:
                version = int(parts[1])
                result.append({
                    "panel_id": parts[0],
                    "version": version,
                    "path": str(f),
                })
            except ValueError:
                pass
    return result


def create_revision_manuscript(
    project_dir: Path,
    panel_id: str,
    current_version: int | None = None,
) -> tuple[int, str]:
    """原本を保持したまま改訂版の新バージョン番号とコンテンツを返す。

    Returns:
        (new_version, original_content)
    """
    if current_version is None:
        current_version = get_latest_manuscript_version(project_dir, panel_id)
    if current_version == 0:
        raise WriterError(f"原稿が存在しません: {panel_id}")
    original_content = load_manuscript(project_dir, panel_id, current_version)
    if original_content is None:
        raise WriterError(f"原稿が見つかりません: {panel_id} v{current_version}")
    return current_version + 1, original_content


def register_manuscript_artifact(
    manifest: ArtifactManifest,
    project_dir: Path,
    panel_id: str,
    version: int = 1,
    title: str = "",
    parent_artifact_id: str | None = None,
) -> Artifact:
    """原稿を artifact-manifest に登録する。"""
    artifact_id = f"{panel_id}-v{version}"
    ms_dir = get_manuscripts_dir(project_dir)
    file_path = str(ms_dir / _manuscript_filename(panel_id, version))
    now = _now_iso()
    artifact = Artifact(
        artifact_id=artifact_id,
        type="manuscript",
        title=title or f"{panel_id} v{version}",
        version=version,
        status="draft",
        file_path=file_path,
        created_at=now,
        updated_at=now,
        parent_artifact_id=parent_artifact_id,
    )
    # 既存エントリがあれば上書き更新
    existing = next((a for a in manifest.artifacts if a.artifact_id == artifact_id), None)
    if existing is not None:
        existing.status = "draft"
        existing.updated_at = now
        return existing
    manifest.artifacts.append(artifact)
    manifest.updated_at = now
    return artifact


def check_prerequisite_approved(manifest: ArtifactManifest, artifact_id: str) -> bool:
    """指定成果物が approved 状態かどうかを確認する。"""
    artifact = next((a for a in manifest.artifacts if a.artifact_id == artifact_id), None)
    if artifact is None:
        return False
    return artifact.status == "approved"
