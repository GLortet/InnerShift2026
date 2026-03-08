from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DEFAULT_SESSION_TITLE, DEFAULT_USER_ID
from modules import storage
from modules.utils import absolute_from_relative, count_words, relative_to_base, utc_now_iso


def build_empty_session(title: str | None = None, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    now = utc_now_iso()
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    return {
        "id": session_id,
        "user_id": user_id,
        "title": title.strip() if title and title.strip() else DEFAULT_SESSION_TITLE,
        "created_at": now,
        "updated_at": now,
        "status": "created",
        "audio": {},
        "transcription": {
            "text": "",
            "language": None,
            "segments": [],
            "word_count": 0,
            "edited": False,
            "warnings": [],
        },
        "analysis": {},
        "report": {},
    }


def create_session(title: str | None = None, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    storage.initialize_storage()
    session = build_empty_session(title=title, user_id=user_id)
    storage.save_session_record(session)
    return session


def load_session(session_id: str | None) -> dict[str, Any] | None:
    if not session_id:
        return None
    return storage.load_session_record(session_id)


def save_session(session: dict[str, Any]) -> dict[str, Any]:
    session["updated_at"] = utc_now_iso()
    storage.save_session_record(session)
    return session


def list_sessions() -> list[dict[str, Any]]:
    storage.initialize_storage()
    return storage.list_session_records()


def update_session_title(session: dict[str, Any], title: str) -> dict[str, Any]:
    session = deepcopy(session)
    session["title"] = title.strip() if title.strip() else session["title"]
    return save_session(session)


def attach_audio(session: dict[str, Any], audio_payload: dict[str, Any]) -> dict[str, Any]:
    session = deepcopy(session)
    session["audio"] = audio_payload
    session["status"] = "audio_ready"
    return save_session(session)


def attach_transcription(session: dict[str, Any], transcription_payload: dict[str, Any]) -> dict[str, Any]:
    session = deepcopy(session)
    session["transcription"] = transcription_payload
    session["status"] = "transcribed"
    storage.save_transcript_text(session["id"], transcription_payload.get("text", ""))
    return save_session(session)


def update_transcription_text(session: dict[str, Any], text: str, edited: bool = True) -> dict[str, Any]:
    session = deepcopy(session)
    session.setdefault("transcription", {})
    session["transcription"]["text"] = text.strip()
    session["transcription"]["word_count"] = count_words(text)
    session["transcription"]["edited"] = edited
    storage.save_transcript_text(session["id"], session["transcription"]["text"])
    return save_session(session)


def attach_analysis(session: dict[str, Any], analysis_payload: dict[str, Any]) -> dict[str, Any]:
    session = deepcopy(session)
    session["analysis"] = analysis_payload
    session["status"] = "analyzed"
    return save_session(session)


def attach_report(session: dict[str, Any], report_payload: dict[str, Any]) -> dict[str, Any]:
    session = deepcopy(session)
    session["report"] = report_payload
    session["status"] = "reported"
    return save_session(session)


def get_preferred_audio_path(session: dict[str, Any]) -> Path | None:
    audio = session.get("audio", {})
    for key in ("normalized_path", "original_path"):
        candidate = absolute_from_relative(audio.get(key))
        if candidate and candidate.exists():
            return candidate
    return None


def get_report_path(session: dict[str, Any]) -> Path | None:
    return absolute_from_relative(session.get("report", {}).get("pdf_path"))


def serializable_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return relative_to_base(path)
