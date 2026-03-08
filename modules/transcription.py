from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from config import (
    WHISPER_BEAM_SIZE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_MODEL_SIZE,
    WHISPER_VAD_FILTER,
)
from modules.utils import count_words

try:
    from faster_whisper import WhisperModel
except Exception as import_error:  # pragma: no cover - handled at runtime
    WhisperModel = None
    FASTER_WHISPER_IMPORT_ERROR = import_error
else:
    FASTER_WHISPER_IMPORT_ERROR = None


class TranscriptionError(RuntimeError):
    """Raised when audio transcription cannot be completed."""


@lru_cache(maxsize=1)
def load_whisper_model() -> Any:
    if WhisperModel is None:
        message = "Le package faster-whisper n'est pas disponible dans l'environnement courant."
        if FASTER_WHISPER_IMPORT_ERROR:
            message = f"{message} Detail: {FASTER_WHISPER_IMPORT_ERROR}"
        raise TranscriptionError(message)
    return WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)


def transcribe_audio(audio_path: str | Path, language_override: str | None = None) -> dict[str, Any]:
    source_path = Path(audio_path)
    if not source_path.exists():
        raise TranscriptionError(f"Fichier audio introuvable : {source_path}")
    if source_path.stat().st_size == 0:
        raise TranscriptionError("Le fichier audio est vide.")

    model = load_whisper_model()
    try:
        segments_iterable, info = model.transcribe(
            str(source_path),
            beam_size=WHISPER_BEAM_SIZE,
            language=language_override or None,
            vad_filter=WHISPER_VAD_FILTER,
            condition_on_previous_text=False,
            word_timestamps=False,
        )
    except Exception as exc:  # pragma: no cover - depends on runtime model and audio
        raise TranscriptionError(f"La transcription Whisper a echoue : {exc}") from exc

    segments: list[dict[str, Any]] = []
    for segment in segments_iterable:
        cleaned_text = " ".join(segment.text.split()).strip()
        if not cleaned_text:
            continue
        segments.append(
            {
                "start": round(float(segment.start), 2),
                "end": round(float(segment.end), 2),
                "text": cleaned_text,
            }
        )

    text = " ".join(item["text"] for item in segments).strip()
    if not text:
        raise TranscriptionError("La transcription n'a produit aucun texte exploitable.")

    warnings: list[str] = []
    language_probability = getattr(info, "language_probability", None)
    if language_probability is not None and language_probability < 0.55:
        warnings.append(
            "La langue detectee est incertaine : une correction manuelle de la transcription peut etre utile."
        )

    detected_language = getattr(info, "language", None) or language_override or "unknown"
    duration = max([item["end"] for item in segments], default=0.0)

    return {
        "text": text,
        "language": detected_language,
        "segments": segments,
        "word_count": count_words(text),
        "edited": False,
        "warnings": warnings,
        "model": WHISPER_MODEL_SIZE,
        "duration_seconds": round(duration, 2),
    }
