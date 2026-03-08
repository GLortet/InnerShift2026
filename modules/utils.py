from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from config import BASE_DIR


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def format_display_datetime(iso_value: str | None) -> str:
    if not iso_value:
        return "N/A"
    try:
        value = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    except ValueError:
        return iso_value
    return value.astimezone().strftime("%d %b %Y, %H:%M")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return normalized or "item"


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def truncate_text(text: str, limit: int = 220, suffix: str = "...") -> str:
    stripped = " ".join(text.split())
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - len(suffix)].rstrip() + suffix


def relative_to_base(path: Path) -> str:
    return str(path.resolve().relative_to(BASE_DIR.resolve()))


def absolute_from_relative(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    return (BASE_DIR / path_value).resolve()


def load_json_file(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def read_text_file(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def safe_float(value: Any, fallback: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def coalesce(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}, ()):
            return value
    return None
