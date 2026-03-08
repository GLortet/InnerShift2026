from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from config import DEFAULT_USER_ID, SCORE_LABELS
from modules import storage
from modules.utils import dedupe_preserve_order, utc_now_iso


def load_profile(user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    storage.initialize_storage()
    return storage.load_profile_record(user_id)


def _derive_progress_signals(score_trends: dict[str, list[dict[str, Any]]]) -> list[str]:
    signals: list[str] = []
    if not score_trends:
        return signals

    positive_mappings = {
        "clarity": "La clarte percue progresse au fil des sessions.",
        "action_orientation": "Le discours devient plus oriente vers l'action.",
        "internal_coherence": "Les sujets evoques semblent gagner en coherence interne.",
    }
    inverse_mappings = {
        "mental_dispersion": "La dispersion mentale diminue progressivement.",
        "emotional_load": "La charge emotionnelle parait mieux contenue qu'au depart.",
    }

    for metric, sentence in positive_mappings.items():
        history = score_trends.get(metric, [])
        if len(history) >= 2 and history[-1]["value"] - history[0]["value"] >= 8:
            signals.append(sentence)

    for metric, sentence in inverse_mappings.items():
        history = score_trends.get(metric, [])
        if len(history) >= 2 and history[0]["value"] - history[-1]["value"] >= 8:
            signals.append(sentence)

    if not signals:
        signals.append("Les tendances restent encore jeunes : quelques sessions supplementaires renforceront la lecture evolutive.")
    return signals[:3]


def rebuild_profile(user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    storage.initialize_storage()
    sessions = [
        session
        for session in storage.list_session_records()
        if session.get("user_id") == user_id and session.get("analysis")
    ]
    sessions.sort(key=lambda item: item.get("created_at") or "")

    if not sessions:
        profile = storage.build_default_profile(user_id)
        profile["updated_at"] = utc_now_iso()
        storage.save_profile_record(profile, user_id)
        return profile

    theme_counter: Counter = Counter()
    keyword_counter: Counter = Counter()
    tone_counter: Counter = Counter()
    score_trends: dict[str, list[dict[str, Any]]] = defaultdict(list)
    recent_recommendations: list[str] = []
    recent_sessions: list[dict[str, Any]] = []

    for session in sessions:
        analysis = session.get("analysis", {})
        for theme in analysis.get("dominant_themes", []):
            theme_counter[theme.get("theme", "")] += int(theme.get("count", 1))
        for keyword in analysis.get("keyword_frequencies", []):
            keyword_counter[keyword.get("term", "")] += int(keyword.get("count", 1))
        for tone in analysis.get("emotional_signals", []):
            tone_counter[tone.get("signal", "")] += int(tone.get("count", 1))
        for score_name, score_value in analysis.get("scores", {}).items():
            score_trends[score_name].append(
                {
                    "session_id": session.get("id"),
                    "title": session.get("title"),
                    "created_at": session.get("created_at"),
                    "value": int(score_value),
                }
            )
        recent_recommendations.extend(analysis.get("recommendations", [])[:2])
        recent_sessions.append(
            {
                "session_id": session.get("id"),
                "title": session.get("title"),
                "created_at": session.get("created_at"),
                "summary": analysis.get("summary", ""),
                "top_theme": (analysis.get("dominant_themes") or [{}])[0].get("theme"),
            }
        )

    profile = {
        "user_id": user_id,
        "updated_at": utc_now_iso(),
        "session_count": len(sessions),
        "top_themes": [
            {"theme": theme, "count": count}
            for theme, count in theme_counter.most_common(6)
            if theme
        ],
        "top_keywords": [
            {"term": term, "count": count}
            for term, count in keyword_counter.most_common(12)
            if term
        ],
        "recurring_tones": [
            {"signal": signal, "count": count}
            for signal, count in tone_counter.most_common(6)
            if signal
        ],
        "score_trends": dict(score_trends),
        "score_labels": SCORE_LABELS,
        "recent_recommendations": dedupe_preserve_order(list(reversed(recent_recommendations)))[:6],
        "progress_signals": _derive_progress_signals(dict(score_trends)),
        "recent_sessions": list(reversed(recent_sessions))[:5],
    }
    storage.save_profile_record(profile, user_id)
    return profile
