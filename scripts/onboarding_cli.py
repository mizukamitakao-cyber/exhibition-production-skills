#!/usr/bin/env python3
"""
Onboardingセッション管理CLI。
exhibition-museum-onboarding スキルから Bash ツール経由で呼ばれる。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.onboarding import (
    build_draft_profile,
    complete_phase,
    create_session,
    get_domain_questions,
    get_next_questions,
    is_phase_complete,
    load_session,
    pause_session,
    record_answer,
    resume_session,
    save_session,
    skip_question,
)
from core.yaml_io import load_yaml_raw, save_yaml


def cmd_create(args: argparse.Namespace) -> None:
    session = create_session(args.museum_id, args.session_id)
    path = Path(args.session_path)
    save_session(session, path)
    print(json.dumps({"status": "created", "session_path": str(path)}))


def cmd_status(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    print(json.dumps({
        "museum_id": session.museum_id,
        "status": session.status,
        "current_phase": session.current_phase,
        "completed_phases": session.completed_phases,
        "answered_count": len(session.answered_questions),
        "skipped_count": len(session.skipped_questions),
        "paused_at": session.paused_at,
        "paused_reason": session.paused_reason,
    }))


def cmd_record_answer(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    record_answer(session, args.question_id, args.answer, args.source)
    save_session(session, Path(args.session_path))
    print(json.dumps({"status": "recorded", "question_id": args.question_id}))


def cmd_skip(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    skip_question(session, args.question_id, args.reason)
    save_session(session, Path(args.session_path))
    print(json.dumps({"status": "skipped", "question_id": args.question_id}))


def cmd_complete_phase(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    questions_config = load_yaml_raw(Path(args.questions_path))
    complete_phase(session, args.phase_name, questions_config)
    save_session(session, Path(args.session_path))
    print(json.dumps({
        "status": "phase_completed",
        "completed_phase": args.phase_name,
        "current_phase": session.current_phase,
        "session_status": session.status,
    }))


def cmd_check_phase(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    questions_config = load_yaml_raw(Path(args.questions_path))
    done = is_phase_complete(session, args.phase_name, questions_config)
    print(json.dumps({"phase": args.phase_name, "is_complete": done}))


def cmd_pause(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    pause_session(session, args.reason)
    save_session(session, Path(args.session_path))
    print(json.dumps({"status": "paused"}))


def cmd_resume(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    resume_session(session)
    save_session(session, Path(args.session_path))
    print(json.dumps({"status": "resumed", "current_phase": session.current_phase}))


def cmd_build_profile(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    questions_config = load_yaml_raw(Path(args.questions_path))
    profile = build_draft_profile(session, questions_config)
    profile.status = "ready_for_review"
    draft_path = Path(args.draft_path)
    save_yaml(draft_path, profile)
    print(json.dumps({"status": "profile_built", "draft_path": str(draft_path)}))


def cmd_next_questions(args: argparse.Namespace) -> None:
    session = load_session(Path(args.session_path))
    questions_config = load_yaml_raw(Path(args.questions_path))
    questions = get_next_questions(session, questions_config, args.count)
    if not questions and not session.current_phase:
        # ドメイン追加質問を試みる
        questions = get_domain_questions(session, questions_config, args.count)
    print(json.dumps({"questions": questions, "current_phase": session.current_phase}))


def main() -> None:
    parser = argparse.ArgumentParser(prog="onboarding_cli", description="Onboardingセッション管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="新規セッションを作成する")
    p.add_argument("--museum-id", required=True)
    p.add_argument("--session-id", required=True)
    p.add_argument("--session-path", required=True)

    p = sub.add_parser("status", help="セッション状態を表示する")
    p.add_argument("--session-path", required=True)

    p = sub.add_parser("record-answer", help="質問への回答を記録する")
    p.add_argument("--session-path", required=True)
    p.add_argument("--question-id", required=True)
    p.add_argument("--answer", required=True)
    p.add_argument("--source", default="hearing")

    p = sub.add_parser("skip", help="質問をスキップする")
    p.add_argument("--session-path", required=True)
    p.add_argument("--question-id", required=True)
    p.add_argument("--reason", default="")

    p = sub.add_parser("complete-phase", help="フェーズを完了してから次へ進む")
    p.add_argument("--session-path", required=True)
    p.add_argument("--phase-name", required=True)
    p.add_argument("--questions-path", required=True)

    p = sub.add_parser("check-phase", help="フェーズの完了状態を確認する")
    p.add_argument("--session-path", required=True)
    p.add_argument("--phase-name", required=True)
    p.add_argument("--questions-path", required=True)

    p = sub.add_parser("pause", help="セッションを中断する")
    p.add_argument("--session-path", required=True)
    p.add_argument("--reason", default="")

    p = sub.add_parser("resume", help="セッションを再開する")
    p.add_argument("--session-path", required=True)

    p = sub.add_parser("build-profile", help="ヒアリング結果からプロファイルドラフトを生成する")
    p.add_argument("--session-path", required=True)
    p.add_argument("--questions-path", required=True)
    p.add_argument("--draft-path", required=True)

    p = sub.add_parser("next-questions", help="次に聞くべき質問を取得する")
    p.add_argument("--session-path", required=True)
    p.add_argument("--questions-path", required=True)
    p.add_argument("--count", type=int, default=3)

    dispatch = {
        "create": cmd_create,
        "status": cmd_status,
        "record-answer": cmd_record_answer,
        "skip": cmd_skip,
        "complete-phase": cmd_complete_phase,
        "check-phase": cmd_check_phase,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "build-profile": cmd_build_profile,
        "next-questions": cmd_next_questions,
    }
    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
