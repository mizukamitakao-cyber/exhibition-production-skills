"""
企画書管理。
Exhibition Planner スキルのPythonサポート。
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.models.artifact_manifest import Artifact, ArtifactManifest
from core.storage import atomic_write
from core.yaml_io import load_yaml, save_yaml


class PlannerError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── ArtifactManifest 管理 ──────────────────────────────────────────────

def create_artifact_manifest(project_id: str) -> ArtifactManifest:
    return ArtifactManifest(project_id=project_id, updated_at=_now_iso())


def add_artifact(manifest: ArtifactManifest, artifact: Artifact) -> ArtifactManifest:
    existing_ids = {a.artifact_id for a in manifest.artifacts}
    if artifact.artifact_id in existing_ids:
        raise PlannerError(f"成果物IDが重複しています: {artifact.artifact_id}")
    manifest.artifacts.append(artifact)
    manifest.updated_at = _now_iso()
    return manifest


def get_artifact(manifest: ArtifactManifest, artifact_id: str) -> Artifact | None:
    return next((a for a in manifest.artifacts if a.artifact_id == artifact_id), None)


def update_artifact_status(
    manifest: ArtifactManifest,
    artifact_id: str,
    status: str,
) -> ArtifactManifest:
    artifact = get_artifact(manifest, artifact_id)
    if artifact is None:
        raise PlannerError(f"成果物が見つかりません: {artifact_id}")
    artifact.status = status  # type: ignore[assignment]
    if status == "approved":
        artifact.approved_at = _now_iso()
    artifact.updated_at = _now_iso()
    manifest.updated_at = _now_iso()
    return manifest


def get_plan_dir(project_dir: Path) -> Path:
    return project_dir / "plan"


def save_artifact_manifest(manifest: ArtifactManifest, project_dir: Path) -> None:
    plan_dir = get_plan_dir(project_dir)
    plan_dir.mkdir(exist_ok=True)
    save_yaml(plan_dir / "artifact-manifest.yaml", manifest)


def load_artifact_manifest(project_dir: Path) -> ArtifactManifest | None:
    path = get_plan_dir(project_dir) / "artifact-manifest.yaml"
    if not path.exists():
        return None
    return load_yaml(path, ArtifactManifest)


# ── 企画書ファイル管理 ────────────────────────────────────────────────

def _plan_filename(version: int) -> str:
    return f"exhibition-plan-v{version}.md"


def save_plan_draft(
    project_dir: Path,
    content: str,
    version: int = 1,
) -> Path:
    """企画書Markdownをアトミックに保存し、パスを返す。"""
    plan_dir = get_plan_dir(project_dir)
    plan_dir.mkdir(exist_ok=True)
    path = plan_dir / _plan_filename(version)
    atomic_write(path, content)
    return path


def load_plan_draft(project_dir: Path, version: int = 1) -> str | None:
    path = get_plan_dir(project_dir) / _plan_filename(version)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def get_latest_plan_version(project_dir: Path) -> int:
    """存在する企画書の最大バージョン番号を返す。存在しない場合は 0。"""
    plan_dir = get_plan_dir(project_dir)
    if not plan_dir.exists():
        return 0
    best = 0
    for f in plan_dir.glob("exhibition-plan-v*.md"):
        try:
            v = int(f.stem.split("-v")[1])
            if v > best:
                best = v
        except (IndexError, ValueError):
            pass
    return best


def register_plan_artifact(
    manifest: ArtifactManifest,
    project_dir: Path,
    version: int = 1,
    title: str = "",
) -> Artifact:
    """企画書を artifact-manifest に登録する。"""
    artifact_id = f"plan-v{version}"
    plan_dir = get_plan_dir(project_dir)
    file_path = str(plan_dir / _plan_filename(version))
    artifact = Artifact(
        artifact_id=artifact_id,
        type="plan",
        title=title or f"企画書 v{version}",
        version=version,
        status="draft",
        file_path=file_path,
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    add_artifact(manifest, artifact)
    return artifact
