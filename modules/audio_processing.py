from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any

from config import AUDIO_DIR, SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_AUDIO_MIME_TYPES
from modules.utils import absolute_from_relative, relative_to_base, safe_float, slugify, utc_now_iso


def infer_extension(filename: str | None, mime_type: str | None = None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in SUPPORTED_AUDIO_EXTENSIONS:
        return suffix
    if mime_type and mime_type in SUPPORTED_AUDIO_MIME_TYPES:
        return SUPPORTED_AUDIO_MIME_TYPES[mime_type]
    return ".wav"


def detect_audio_mime_type(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".mpeg": "audio/mpeg",
    }.get(suffix, "audio/wav")


def probe_audio_duration(path: Path) -> float | None:
    if not path.exists():
        return None

    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as wav_handle:
                frames = wav_handle.getnframes()
                rate = wav_handle.getframerate() or 1
                return round(frames / float(rate), 2)
        except (wave.Error, OSError):
            pass

    if shutil.which("ffprobe"):
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return safe_float(result.stdout.strip())
    return None


def normalize_audio(input_path: Path, session_id: str) -> tuple[Path | None, list[str]]:
    warnings: list[str] = []
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        warnings.append("ffmpeg est introuvable : l'audio original sera utilise sans normalisation.")
        return None, warnings

    output_path = AUDIO_DIR / f"{session_id}_normalized.wav"
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        warnings.append("La normalisation audio a echoue : utilisation du fichier original.")
        return None, warnings
    return output_path, warnings


def save_streamlit_audio(uploaded_file: Any, session_id: str, source: str) -> dict[str, Any]:
    if uploaded_file is None:
        raise ValueError("Aucun fichier audio n'a ete fourni.")

    raw_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    if not raw_bytes:
        raise ValueError("Le contenu audio est vide.")

    original_name = getattr(uploaded_file, "name", None) or f"{source}.wav"
    mime_type = getattr(uploaded_file, "type", None)
    extension = infer_extension(original_name, mime_type)
    safe_stem = slugify(Path(original_name).stem or source)
    original_path = AUDIO_DIR / f"{session_id}_{source}_{safe_stem}{extension}"
    original_path.write_bytes(raw_bytes)

    duration = probe_audio_duration(original_path)
    normalized_path, warnings = normalize_audio(original_path, session_id)
    normalized_duration = probe_audio_duration(normalized_path) if normalized_path else None

    return {
        "source": source,
        "original_filename": original_name,
        "original_path": relative_to_base(original_path),
        "normalized_path": relative_to_base(normalized_path) if normalized_path else None,
        "format": extension.lstrip("."),
        "mime_type": mime_type or detect_audio_mime_type(original_path),
        "size_bytes": len(raw_bytes),
        "duration_seconds": normalized_duration or duration,
        "saved_at": utc_now_iso(),
        "warnings": warnings,
    }


def load_audio_bytes(path_value: str | Path | None) -> bytes | None:
    if path_value is None:
        return None
    path = absolute_from_relative(path_value) if isinstance(path_value, str) else path_value
    if not path or not path.exists():
        return None
    return path.read_bytes()
