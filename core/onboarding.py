"""
Onboardingセッション状態機械。
設計仕様: docs/design/04_ONBOARDING_DESIGN.md
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.models.museum_profile import MuseumProfile
from core.models.onboarding_session import (
    AnsweredQuestion,
    OnboardingSession,
    PendingQuestion,
    SkippedQuestion,
)
from core.yaml_io import load_yaml, load_yaml_raw, save_yaml

PHASE_ORDER = [
    "basic",
    "visitors",
    "exhibition_policy",
    "research",
    "writing",
    "design",
    "quality",
    "operations",
]

# フィールドパスから値の型を引くマッピング
FIELD_TYPES: dict[str, str] = {
    "basic.name": "string",
    "basic.type": "string",
    "basic.purpose": "string",
    "basic.domains": "list",
    "visitors.target_groups": "list",
    "visitors.languages": "list",
    "visitors.accessibility_requirements": "list",
    "exhibition_policy.purpose": "string",
    "exhibition_policy.education_policy": "string",
    "exhibition_policy.key_themes": "list",
    "exhibition_policy.content_restrictions": "list",
    "research.priority_sources": "list",
    "research.citation_style": "string",
    "research.unverified_handling": "string",
    "research.ai_content_policy": "string",
    "writing.style": "string",
    "writing.honorific_level": "string",
    "writing.max_chars_panel": "int",
    "writing.max_chars_caption": "int",
    "writing.vocabulary": "dict_note",
    "writing.notation_rules": "list",
    "design.design_guide_path": "string",
    "design.panel_specs": "dict_note",
    "quality.advocate_criteria": "list",
    "quality.reviewer_criteria": "list",
    "operations.approval_flow": "list",
    "operations.roles": "dict_note",
    "operations.output_formats": "list",
    "data_management.ai_input_restrictions": "list",
}

# 専門分野キーワード → domain_questions キー のマッピング
DOMAIN_KEYWORD_MAP: dict[str, str] = {
    "歴史": "history",
    "history": "history",
    "美術": "art",
    "アート": "art",
    "art": "art",
    "自然史": "natural_history",
    "自然": "natural_history",
    "natural_history": "natural_history",
    "natural-history": "natural_history",
    "科学": "science",
    "science": "science",
    "理工": "science",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(museum_id: str, session_id: str) -> OnboardingSession:
    """新しいOnboardingセッションを作成する（in_progress状態）。"""
    now = _now_iso()
    return OnboardingSession(
        session_id=session_id,
        museum_id=museum_id,
        status="in_progress",
        created_at=now,
        updated_at=now,
        current_phase="basic",
    )


def load_session(session_path: Path) -> OnboardingSession:
    """onboarding-session.yaml からセッションを読み込む。"""
    return load_yaml(session_path, OnboardingSession)


def save_session(session: OnboardingSession, session_path: Path) -> None:
    """セッションをonboarding-session.yaml にアトミックに保存する。"""
    session.updated_at = _now_iso()
    save_yaml(session_path, session)


def get_answered_ids(session: OnboardingSession) -> set[str]:
    answered = {q.question_id for q in session.answered_questions}
    skipped = {q.question_id for q in session.skipped_questions}
    return answered | skipped


def get_next_questions(
    session: OnboardingSession,
    questions_config: dict,
    count: int = 3,
) -> list[dict]:
    """
    現在フェーズから未回答の質問を最大 count 件返す。
    現在フェーズが空（全フェーズ完了）の場合は空リストを返す。
    """
    answered = get_answered_ids(session)
    phase_id = session.current_phase
    if not phase_id:
        return []

    phases_map = {p["phase_id"]: p for p in questions_config.get("phases", [])}
    phase = phases_map.get(phase_id)
    if not phase:
        return []

    result: list[dict] = []
    for q in phase.get("questions", []):
        if q["id"] not in answered:
            result.append(q)
            if len(result) >= count:
                break

    return result


def get_domain_questions(
    session: OnboardingSession,
    questions_config: dict,
    count: int = 3,
) -> list[dict]:
    """
    basic フェーズ完了後に、回答済み専門分野に対応する追加質問を返す。
    """
    answered = get_answered_ids(session)
    domains = _get_domains_from_session(session)
    result: list[dict] = []
    for domain_key in domains:
        for q in questions_config.get("domain_questions", {}).get(domain_key, []):
            if q["id"] not in answered:
                result.append(q)
                if len(result) >= count:
                    return result
    return result


def _get_domains_from_session(session: OnboardingSession) -> list[str]:
    """セッションの回答から basic.domains（正規化済み）を取得する。"""
    for aq in session.answered_questions:
        if aq.question_id == "B-04":
            raw_items = [
                item.strip()
                for item in aq.answer.replace("、", ",").split(",")
                if item.strip()
            ]
            return [
                DOMAIN_KEYWORD_MAP.get(item, item)
                for item in raw_items
            ]
    return []


def record_answer(
    session: OnboardingSession,
    question_id: str,
    answer: str,
    source: str = "hearing",
) -> OnboardingSession:
    """質問への回答を記録する。同一question_idへの再記録は上書き。"""
    for aq in session.answered_questions:
        if aq.question_id == question_id:
            aq.answer = answer
            aq.answered_at = _now_iso()
            aq.source = source
            session.updated_at = _now_iso()
            return session

    session.answered_questions.append(
        AnsweredQuestion(
            question_id=question_id,
            answer=answer,
            answered_at=_now_iso(),
            source=source,
        )
    )
    session.updated_at = _now_iso()
    return session


def skip_question(
    session: OnboardingSession,
    question_id: str,
    reason: str = "",
) -> OnboardingSession:
    """質問をスキップ（後で再確認）として記録する。"""
    skipped_ids = {q.question_id for q in session.skipped_questions}
    if question_id not in skipped_ids:
        session.skipped_questions.append(
            SkippedQuestion(question_id=question_id, reason=reason)
        )
    session.updated_at = _now_iso()
    return session


def complete_phase(
    session: OnboardingSession,
    phase_name: str,
    questions_config: dict,
) -> OnboardingSession:
    """
    フェーズを完了としてマークし、次フェーズへ進む。
    全フェーズ完了後は status を ready_for_review へ遷移する。
    """
    if phase_name not in session.completed_phases:
        session.completed_phases.append(phase_name)

    idx = PHASE_ORDER.index(phase_name) if phase_name in PHASE_ORDER else -1
    if idx >= 0 and idx + 1 < len(PHASE_ORDER):
        session.current_phase = PHASE_ORDER[idx + 1]
    else:
        session.current_phase = ""
        session.status = "ready_for_review"

    session.updated_at = _now_iso()
    return session


def pause_session(
    session: OnboardingSession,
    reason: str = "",
) -> OnboardingSession:
    """セッションを中断状態にする。"""
    session.status = "paused"
    session.paused_at = _now_iso()
    session.paused_reason = reason
    session.updated_at = _now_iso()
    return session


def resume_session(session: OnboardingSession) -> OnboardingSession:
    """セッションを再開状態にする。"""
    session.status = "in_progress"
    session.paused_at = None
    session.paused_reason = ""
    session.updated_at = _now_iso()
    return session


def is_phase_complete(
    session: OnboardingSession,
    phase_id: str,
    questions_config: dict,
) -> bool:
    """フェーズ内の全必須質問が回答済みかを確認する（skipped は「未回答」扱い）。"""
    answered_only = {q.question_id for q in session.answered_questions}
    phases_map = {p["phase_id"]: p for p in questions_config.get("phases", [])}
    phase = phases_map.get(phase_id)
    if not phase:
        return True

    for q in phase.get("questions", []):
        if q.get("required", False) and q["id"] not in answered_only:
            return False
    return True


def _set_field_value(profile: MuseumProfile, field_path: str, raw_value: str) -> None:
    """dot-notation フィールドパスでMuseumProfileにフィールド値を設定する。"""
    field_type = FIELD_TYPES.get(field_path, "string")
    parts = field_path.split(".")
    obj: Any = profile
    for part in parts[:-1]:
        obj = getattr(obj, part, obj)

    target_attr = parts[-1]
    if field_type == "string":
        setattr(obj, target_attr, raw_value)
    elif field_type == "list":
        items = [
            item.strip()
            for item in raw_value.replace("、", ",").split(",")
            if item.strip()
        ]
        setattr(obj, target_attr, items)
    elif field_type == "int":
        digits = "".join(c for c in raw_value if c.isdigit())
        setattr(obj, target_attr, int(digits) if digits else None)
    elif field_type == "dict_note":
        existing = getattr(obj, target_attr, {})
        if isinstance(existing, dict):
            existing["_note"] = raw_value
            setattr(obj, target_attr, existing)


def build_draft_profile(
    session: OnboardingSession,
    questions_config: dict,
) -> MuseumProfile:
    """
    セッションのヒアリング結果から館別プロファイルのドラフトを構築する。
    - 担当者が回答したフィールドのみ設定する
    - AIが推測した値は登録しない
    """
    now = _now_iso()
    profile = MuseumProfile(
        museum_id=session.museum_id,
        status="draft",
        created_at=session.created_at or now,
        updated_at=now,
    )

    q_map: dict[str, dict] = {}
    for phase_data in questions_config.get("phases", []):
        for q in phase_data.get("questions", []):
            q_map[q["id"]] = q
    for domain_qs in questions_config.get("domain_questions", {}).values():
        for q in domain_qs:
            q_map[q["id"]] = q

    for answered in session.answered_questions:
        q_def = q_map.get(answered.question_id)
        if not q_def:
            continue
        field = q_def.get("field")
        if field and answered.answer.strip():
            try:
                _set_field_value(profile, field, answered.answer.strip())
            except (AttributeError, TypeError):
                pass

    return profile
