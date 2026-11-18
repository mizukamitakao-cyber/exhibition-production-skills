#!/usr/bin/env python3
"""Pydantic モデルから JSON Schema を自動生成する。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"


def generate_schemas() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))

    from core.models.museum_profile import MuseumProfile
    from core.models.profile_evidence import ProfileEvidence
    from core.models.onboarding_session import OnboardingSession
    from core.models.exhibition_project import ExhibitionProject
    from core.models.artifact_manifest import ArtifactManifest
    from core.models.source_registry import SourceRegistry
    from core.models.review_record import ReviewRecord
    from core.models.approval_record import ApprovalRecord
    from core.models.operation_record import OperationRecord

    models = [
        ("museum-profile", MuseumProfile),
        ("profile-evidence", ProfileEvidence),
        ("onboarding-session", OnboardingSession),
        ("exhibition-project", ExhibitionProject),
        ("artifact-manifest", ArtifactManifest),
        ("source-registry", SourceRegistry),
        ("review-record", ReviewRecord),
        ("approval-record", ApprovalRecord),
        ("operation-record", OperationRecord),
    ]

    SCHEMAS_DIR.mkdir(exist_ok=True)

    for name, model in models:
        schema = model.model_json_schema()
        output_path = SCHEMAS_DIR / f"{name}.schema.json"
        output_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"生成: {output_path.relative_to(PROJECT_ROOT)}")

    print(f"\n{len(models)} 件のスキーマを生成しました → {SCHEMAS_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    generate_schemas()
