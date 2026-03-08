from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from config import (
    AUDIO_DIR,
    DEFAULT_PROFILE_PATH,
    DEFAULT_USER_ID,
    DIRECTORIES,
    PROFILE_EMPTY_STATE,
    REPORTS_DIR,
    SESSIONS_DIR,
    TRANSCRIPTS_DIR,
)
from modules.utils import ensure_directories, load_json_file, save_json_file, write_text_file


def initialize_storage() -> None:
    ensure_directories(DIRECTORIES)
    if not DEFAULT_PROFILE_PATH.exists():
        save_json_file(DEFAULT_PROFILE_PATH, build_default_profile(DEFAULT_USER_ID))


def build_default_profile(user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    profile = deepcopy(PROFILE_EMPTY_STATE)
    profile["user_id"] = user_id
    return profile


def session_file_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def transcript_file_path(session_id: str) -> Path:
    return TRANSCRIPTS_DIR / f"{session_id}.txt"


def report_file_path(session_id: str, filename: str) -> Path:
    return REPORTS_DIR / filename.replace("{session_id}", session_id)


def save_session_record(session: dict[str, Any]) -> Path:
    target = session_file_path(session["id"])
    save_json_file(target, session)
    return target


def load_session_record(session_id: str) -> dict[str, Any] | None:
    return load_json_file(session_file_path(session_id))


def list_session_records() -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    for path in sorted(SESSIONS_DIR.glob("*.json")):
        session = load_json_file(path)
        if session:
            sessions.append(session)
    sessions.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return sessions


def save_profile_record(profile: dict[str, Any], user_id: str = DEFAULT_USER_ID) -> Path:
    target = DEFAULT_PROFILE_PATH if user_id == DEFAULT_USER_ID else DEFAULT_PROFILE_PATH.with_name(f"{user_id}.json")
    save_json_file(target, profile)
    return target


def load_profile_record(user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    target = DEFAULT_PROFILE_PATH if user_id == DEFAULT_USER_ID else DEFAULT_PROFILE_PATH.with_name(f"{user_id}.json")
    return load_json_file(target, build_default_profile(user_id))


def save_transcript_text(session_id: str, text: str) -> Path:
    target = transcript_file_path(session_id)
    write_text_file(target, text)
    return target


def list_report_files() -> list[Path]:
    return sorted(REPORTS_DIR.glob("*.pdf"))


def list_audio_files() -> list[Path]:
    return sorted(AUDIO_DIR.glob("*"))
