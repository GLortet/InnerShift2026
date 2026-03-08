from __future__ import annotations

from typing import Any

from modules.questionnaire_schema import MODULE_SCHEMAS

RISK_FIELDS = ["immediate_danger", "harm_thoughts", "unable_to_function"]


def evaluate_safety(safety_answers: dict[str, str]) -> dict[str, Any]:
    risk_flags = [field for field in RISK_FIELDS if safety_answers.get(field) == "yes"]
    asked_human_support = safety_answers.get("support_preference") == "I would prefer human support"
    blocked = bool(risk_flags or asked_human_support)
    return {
        "blocked": blocked,
        "risk_flags": risk_flags,
        "asked_human_support": asked_human_support,
    }


def get_module_for_orientation(orientation: str | None) -> dict[str, Any]:
    if not orientation:
        return {}
    return MODULE_SCHEMAS.get(orientation, {})


def _safe_text(value: Any, fallback: str = "Not specified") -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def compute_onboarding_insights(payload: dict[str, Any]) -> dict[str, Any]:
    intention = payload.get("intention", {})
    orientation = payload.get("orientation", {})
    module = payload.get("module", {})
    module_answers = module.get("answers", {})

    dominant_intention = _safe_text(intention.get("session_outcome") or intention.get("topic"))
    current_load = _safe_text(intention.get("heaviest_part"))

    needs_candidates = [
        module_answers.get("lacking"),
        module_answers.get("low_need"),
        module_answers.get("need_to_express"),
        intention.get("help_type"),
    ]
    current_needs = [item for item in needs_candidates if item]

    relational_posture = _safe_text(
        module_answers.get("posture") or "Grounded and respectful posture to preserve"
    )

    dominant_mode = _safe_text(
        orientation.get("area") or "guided reflection",
        fallback="guided reflection",
    )

    action_24h = _safe_text(
        module_answers.get("next_24h_action")
        or module_answers.get("smallest_next_decision")
        or module_answers.get("recovery_tomorrow")
        or module_answers.get("commitment")
    )
    action_7d = _safe_text("Protect one focused block to test your action and collect feedback.")
    action_30d = _safe_text("Review what worked, what drained you, and reset your recentering plan.")

    tensions = [
        item
        for item in [
            module_answers.get("loops"),
            module_answers.get("main_block"),
            module_answers.get("assumption"),
            module_answers.get("under_pressure"),
        ]
        if item
    ]

    stress_signals = [
        item
        for item in [
            module_answers.get("pressure_reaction"),
            module_answers.get("disconnect"),
            module_answers.get("stop_doing"),
        ]
        if item
    ]

    strengths = [
        item
        for item in [
            module_answers.get("recenter"),
            module_answers.get("nourishes"),
            module_answers.get("recognized_qualities"),
            module_answers.get("helpful_environment"),
        ]
        if item
    ]

    actions_to_test = [
        item
        for item in [
            action_24h,
            module_answers.get("respectful_sentence"),
            module_answers.get("commitment"),
            module_answers.get("stop_doing"),
        ]
        if item and item != "Not specified"
    ]

    return {
        "session_topic": _safe_text(intention.get("topic")),
        "dominant_intention": dominant_intention,
        "current_load": current_load,
        "current_needs": current_needs[:3] or ["clarity"],
        "likely_relational_posture": relational_posture,
        "dominant_functioning_mode": dominant_mode,
        "action_plan": {
            "next_24h": action_24h,
            "next_7_days": action_7d,
            "next_30_days": action_30d,
        },
        "main_tensions": tensions[:3],
        "possible_stress_signals": stress_signals[:3],
        "strengths_resources": strengths[:3],
        "actions_to_test": actions_to_test[:3],
    }
