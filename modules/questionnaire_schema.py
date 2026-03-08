from __future__ import annotations

from typing import Any

from config import (
    CONTINUATION_OPTIONS,
    ORIENTATION_OPTIONS,
    SAFETY_HELP_OPTIONS,
    SESSION_HELP_OPTIONS,
)

SAFETY_SCHEMA: list[dict[str, Any]] = [
    {
        "id": "main_help",
        "label": "What do you mainly want help with today?",
        "type": "choice",
        "options": SAFETY_HELP_OPTIONS,
    },
    {
        "id": "immediate_danger",
        "label": "Are you currently in immediate danger or in an emergency situation?",
        "type": "choice",
        "options": ["no", "yes"],
    },
    {
        "id": "harm_thoughts",
        "label": "Are you having thoughts of hurting yourself or someone else?",
        "type": "choice",
        "options": ["no", "yes"],
    },
    {
        "id": "unable_to_function",
        "label": "Do you feel so overwhelmed that you are unable to function?",
        "type": "choice",
        "options": ["no", "yes"],
    },
    {
        "id": "support_preference",
        "label": "Would you prefer to continue with a self-reflection tool, or would you prefer human support?",
        "type": "choice",
        "options": ["continue with the tool", "I would prefer human support"],
    },
]

INTENTION_SCHEMA: list[dict[str, Any]] = [
    {"id": "topic", "label": "What topic would you like to clarify today?", "type": "short_text"},
    {
        "id": "heaviest_part",
        "label": "What feels most heavy or most important about this topic right now?",
        "type": "long_text",
    },
    {
        "id": "session_outcome",
        "label": "What would you like to obtain by the end of this session?",
        "type": "short_text",
    },
    {
        "id": "help_type",
        "label": "What kind of help would be most useful right now?",
        "type": "choice",
        "options": SESSION_HELP_OPTIONS,
    },
    {
        "id": "continuation_mode",
        "label": "How would you like to continue?",
        "type": "choice",
        "options": CONTINUATION_OPTIONS,
    },
]

ORIENTATION_SCHEMA: dict[str, Any] = {
    "id": "orientation_area",
    "label": "Which area best matches what you are experiencing right now?",
    "type": "choice",
    "options": ORIENTATION_OPTIONS,
}

MODULE_SCHEMAS: dict[str, dict[str, Any]] = {
    "overload / stress": {
        "title": "Stress / overload",
        "goal": "Identify overload, current needs, and recentering actions.",
        "questions": [
            {"id": "drains", "label": "What drains you the most right now?", "type": "long_text"},
            {"id": "loops", "label": "What keeps looping in your mind?", "type": "long_text"},
            {
                "id": "lacking",
                "label": "What do you feel you are lacking most right now?",
                "type": "choice",
                "options": ["calm", "recognition", "structure", "support", "movement", "time alone", "stimulation"],
            },
            {
                "id": "pressure_reaction",
                "label": "How do you usually react when pressure rises?",
                "type": "choice",
                "options": ["I over-adapt", "I criticize", "I shut down", "I get agitated", "I avoid", "I push through"],
            },
            {"id": "recenter", "label": "What usually helps you come back to yourself?", "type": "long_text"},
            {"id": "next_24h_action", "label": "What small realistic action could you do in the next 24 hours?", "type": "short_text"},
        ],
    },
    "hesitation / decision": {
        "title": "Decision",
        "goal": "Clarify the decision, obstacles, criteria, and next step.",
        "questions": [
            {"id": "decision_focus", "label": "What decision or non-decision is occupying your mind?", "type": "long_text"},
            {"id": "options", "label": "What real options do you currently have?", "type": "long_text"},
            {
                "id": "main_block",
                "label": "What blocks you the most?",
                "type": "choice",
                "options": [
                    "fear of making the wrong choice",
                    "fear of disappointing others",
                    "lack of information",
                    "lack of energy",
                    "conflict of values",
                    "need to control everything",
                ],
            },
            {
                "id": "main_criterion",
                "label": "What criterion matters most right now?",
                "type": "choice",
                "options": ["safety", "coherence", "relationship", "impact", "freedom", "effectiveness"],
            },
            {"id": "if_nothing", "label": "What happens if you do nothing for 30 days?", "type": "long_text"},
            {"id": "smallest_next_decision", "label": "What is the smallest next decision, not the final decision?", "type": "short_text"},
        ],
    },
    "conflict / relationship": {
        "title": "Relationship / conflict",
        "goal": "Identify relational posture, assumptions, needs, and communication direction.",
        "questions": [
            {"id": "person", "label": "With whom is the situation difficult?", "type": "short_text"},
            {"id": "facts", "label": "What happened factually?", "type": "long_text"},
            {"id": "felt", "label": "What did you feel?", "type": "long_text"},
            {"id": "assumption", "label": "What did you assume about the other person?", "type": "long_text"},
            {
                "id": "posture",
                "label": "What best describes your current relational posture?",
                "type": "choice",
                "options": [
                    "I feel legitimate and I still value the other person",
                    "I feel above the other person",
                    "I feel below the other person",
                    "I feel threatened",
                ],
            },
            {"id": "need_to_express", "label": "What do you need to express more clearly?", "type": "long_text"},
            {"id": "tone", "label": "What tone would be most appropriate?", "type": "choice", "options": ["warm", "factual", "direct", "expressive"]},
            {"id": "respectful_sentence", "label": "What simple respectful sentence could you say?", "type": "short_text"},
        ],
    },
    "low energy / motivation": {
        "title": "Energy / motivation",
        "goal": "Identify what restores energy and what is missing.",
        "questions": [
            {"id": "disconnect", "label": "What is making you disconnect right now?", "type": "long_text"},
            {"id": "nourishes", "label": "What genuinely nourishes you when you are doing well?", "type": "long_text"},
            {
                "id": "low_need",
                "label": "Which of these needs feels too low today?",
                "type": "choice",
                "options": [
                    "being appreciated for who I am",
                    "feeling that I produce something useful",
                    "connection and fun",
                    "calm and space",
                    "defending what matters to me",
                    "challenge and intensity",
                ],
            },
            {"id": "missing_week", "label": "In your current week, what is missing the most?", "type": "long_text"},
            {"id": "recovery_tomorrow", "label": "What small dose of recovery could you schedule tomorrow?", "type": "short_text"},
            {"id": "stop_doing", "label": "What should you stop doing to recover energy?", "type": "short_text"},
        ],
    },
    "identity / alignment": {
        "title": "Alignment / identity",
        "goal": "Clarify how you function at your best versus under pressure.",
        "questions": [
            {"id": "best_functioning", "label": "When you are at your best, how do you function?", "type": "long_text"},
            {"id": "recognized_qualities", "label": "What qualities do others recognize in you?", "type": "long_text"},
            {"id": "current_pride", "label": "What makes you proud of yourself right now?", "type": "long_text"},
            {"id": "under_pressure", "label": "Under pressure, what becomes less fair or less accurate in your behavior?", "type": "long_text"},
            {"id": "helpful_environment", "label": "What kind of environment helps you function well?", "type": "long_text"},
            {"id": "protect", "label": "What do you want to protect in yourself in the coming weeks?", "type": "long_text"},
            {"id": "commitment", "label": "What concrete commitment do you make to yourself now?", "type": "short_text"},
        ],
    },
}
