"""core.onboarding の単体テスト"""
from __future__ import annotations

from pathlib import Path

from core.onboarding import (
    PHASE_ORDER,
    build_draft_profile,
    complete_phase,
    create_session,
    get_answered_ids,
    get_next_questions,
    is_phase_complete,
    pause_session,
    record_answer,
    resume_session,
    save_session,
    skip_question,
    load_session,
)

# テスト用の最小 questions_config
_MINIMAL_QUESTIONS: dict = {
    "version": "1.0",
    "phases": [
        {
            "phase_id": "basic",
            "display_name": "基本情報",
            "priority": "required",
            "questions": [
                {
                    "id": "B-01",
                    "text": "館の正式名称を教えてください。",
                    "field": "basic.name",
                    "field_type": "string",
                    "required": True,
                },
                {
                    "id": "B-02",
                    "text": "施設の種別はどれですか。",
                    "field": "basic.type",
                    "field_type": "string",
                    "required": True,
                },
                {
                    "id": "B-03",
                    "text": "施設の設置目的を教えてください。",
                    "field": "basic.purpose",
                    "field_type": "string",
                    "required": False,
                },
            ],
        },
        {
            "phase_id": "visitors",
            "display_name": "来館者",
            "priority": "required",
            "questions": [
                {
                    "id": "V-01",
                    "text": "主な来館者層を教えてください。",
                    "field": "visitors.target_groups",
                    "field_type": "list",
                    "required": True,
                },
            ],
        },
    ],
    "domain_questions": {
        "history": [
            {
                "id": "DH-01",
                "text": "年代の表記方式を教えてください。",
                "field": "writing.notation_rules",
                "field_type": "list",
                "required": False,
            }
        ]
    },
}


class TestCreateSession:
    def test_creates_in_progress(self) -> None:
        session = create_session("museum-001", "session-001")
        assert session.status == "in_progress"
        assert session.museum_id == "museum-001"
        assert session.current_phase == "basic"
        assert session.created_at != ""

    def test_starts_with_empty_answers(self) -> None:
        session = create_session("museum-001", "session-001")
        assert session.answered_questions == []
        assert session.skipped_questions == []


class TestRecordAnswer:
    def test_records_new_answer(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館")
        assert len(session.answered_questions) == 1
        assert session.answered_questions[0].answer == "架空歴史館"

    def test_updates_existing_answer(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "旧名称")
        record_answer(session, "B-01", "新名称")
        assert len(session.answered_questions) == 1
        assert session.answered_questions[0].answer == "新名称"

    def test_records_source(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館", source="document")
        assert session.answered_questions[0].source == "document"


class TestSkipQuestion:
    def test_skips_question(self) -> None:
        session = create_session("museum-001", "session-001")
        skip_question(session, "B-03", "後で確認")
        assert len(session.skipped_questions) == 1
        assert session.skipped_questions[0].question_id == "B-03"

    def test_no_duplicate_skip(self) -> None:
        session = create_session("museum-001", "session-001")
        skip_question(session, "B-03", "後で")
        skip_question(session, "B-03", "後で再度")
        assert len(session.skipped_questions) == 1


class TestGetAnsweredIds:
    def test_includes_both_answered_and_skipped(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "テスト")
        skip_question(session, "B-02", "")
        ids = get_answered_ids(session)
        assert "B-01" in ids
        assert "B-02" in ids


class TestGetNextQuestions:
    def test_returns_unanswered_questions(self) -> None:
        session = create_session("museum-001", "session-001")
        questions = get_next_questions(session, _MINIMAL_QUESTIONS, count=3)
        assert len(questions) == 3
        assert questions[0]["id"] == "B-01"

    def test_skips_answered_questions(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館")
        questions = get_next_questions(session, _MINIMAL_QUESTIONS, count=3)
        ids = [q["id"] for q in questions]
        assert "B-01" not in ids
        assert "B-02" in ids

    def test_respects_count_limit(self) -> None:
        session = create_session("museum-001", "session-001")
        questions = get_next_questions(session, _MINIMAL_QUESTIONS, count=1)
        assert len(questions) == 1

    def test_returns_empty_when_phase_empty(self) -> None:
        session = create_session("museum-001", "session-001")
        session.current_phase = ""
        questions = get_next_questions(session, _MINIMAL_QUESTIONS)
        assert questions == []


class TestCompletePhase:
    def test_advances_to_next_phase(self) -> None:
        session = create_session("museum-001", "session-001")
        complete_phase(session, "basic", _MINIMAL_QUESTIONS)
        assert session.current_phase == "visitors"
        assert "basic" in session.completed_phases

    def test_all_phases_complete_sets_ready_for_review(self) -> None:
        session = create_session("museum-001", "session-001")
        for phase in PHASE_ORDER:
            complete_phase(session, phase, _MINIMAL_QUESTIONS)
        assert session.status == "ready_for_review"
        assert session.current_phase == ""

    def test_last_defined_phase_completes(self) -> None:
        session = create_session("museum-001", "session-001")
        # 最後のフェーズ（PHASE_ORDER[-1]）を直接完了する
        session.current_phase = PHASE_ORDER[-1]
        complete_phase(session, PHASE_ORDER[-1], _MINIMAL_QUESTIONS)
        assert session.status == "ready_for_review"


class TestPauseAndResume:
    def test_pause_sets_status(self) -> None:
        session = create_session("museum-001", "session-001")
        pause_session(session, "担当者が中断を指示")
        assert session.status == "paused"
        assert session.paused_at is not None
        assert session.paused_reason == "担当者が中断を指示"

    def test_resume_clears_pause(self) -> None:
        session = create_session("museum-001", "session-001")
        pause_session(session, "中断")
        resume_session(session)
        assert session.status == "in_progress"
        assert session.paused_at is None


class TestIsPhaseComplete:
    def test_required_answered_returns_true(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館")
        record_answer(session, "B-02", "博物館")
        # B-03 は required: False なのでスキップしても完了
        assert is_phase_complete(session, "basic", _MINIMAL_QUESTIONS) is True

    def test_required_missing_returns_false(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館")
        # B-02 (required) が未回答
        assert is_phase_complete(session, "basic", _MINIMAL_QUESTIONS) is False

    def test_skipped_required_returns_false(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館")
        skip_question(session, "B-02", "後で")
        # B-02 は skip されているが required なので未完了
        assert is_phase_complete(session, "basic", _MINIMAL_QUESTIONS) is False


class TestBuildDraftProfile:
    def test_string_field_set(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館")
        profile = build_draft_profile(session, _MINIMAL_QUESTIONS)
        assert profile.museum_id == "museum-001"
        assert profile.basic.name == "架空歴史館"

    def test_list_field_set(self) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "V-01", "一般市民、小中学生")
        profile = build_draft_profile(session, _MINIMAL_QUESTIONS)
        assert "一般市民" in profile.visitors.target_groups
        assert "小中学生" in profile.visitors.target_groups

    def test_unanswered_field_stays_default(self) -> None:
        session = create_session("museum-001", "session-001")
        profile = build_draft_profile(session, _MINIMAL_QUESTIONS)
        assert profile.basic.name == ""  # デフォルト値のまま

    def test_draft_status_is_draft(self) -> None:
        session = create_session("museum-001", "session-001")
        profile = build_draft_profile(session, _MINIMAL_QUESTIONS)
        assert profile.status == "draft"


class TestSaveAndLoadSession:
    def test_roundtrip(self, tmp_path: Path) -> None:
        session = create_session("museum-001", "session-001")
        record_answer(session, "B-01", "架空歴史館")
        path = tmp_path / "museum-001" / "onboarding-session.yaml"
        save_session(session, path)
        loaded = load_session(path)
        assert loaded.museum_id == "museum-001"
        assert loaded.answered_questions[0].answer == "架空歴史館"
