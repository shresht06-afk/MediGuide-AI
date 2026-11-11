"""
Structured clinical assessment definitions and generation for MediGuide AI v2.0.

Provides validated, structured question templates for common symptom categories
so users can easily provide clinical intake context via clickable options.
"""

from __future__ import annotations

import re
from typing import Any

from .safety import assess_input


STOMACH_ASSESSMENT: dict[str, Any] = {
    "id": "stomach_pain_intake",
    "title": "Quick Symptom Assessment: Stomach & Abdomen",
    "questions": [
        {
            "id": "location",
            "label": "Where is the pain located?",
            "type": "single_choice",
            "options": [
                "Upper abdomen",
                "Lower abdomen",
                "Left side",
                "Right side",
                "Around belly button",
                "Across the abdomen",
                "Not sure",
                "Other",
            ],
        },
        {
            "id": "severity",
            "label": "Pain severity (1 = very mild, 10 = severe)",
            "type": "slider",
            "min": 1,
            "max": 10,
            "default": 5,
        },
        {
            "id": "onset",
            "label": "When did it start?",
            "type": "single_choice",
            "options": [
                "Just started",
                "Today",
                "Yesterday",
                "A few days ago",
                "More than a week ago",
                "Not sure",
            ],
        },
        {
            "id": "associated",
            "label": "Associated symptoms (select all that apply)",
            "type": "multi_choice",
            "options": [
                "Nausea",
                "Vomiting",
                "Fever",
                "Diarrhoea",
                "Constipation",
                "Bloating",
                "Dizziness",
                "None of these",
                "Other",
            ],
        },
    ],
}

HEADACHE_ASSESSMENT: dict[str, Any] = {
    "id": "headache_intake",
    "title": "Quick Symptom Assessment: Headache",
    "questions": [
        {
            "id": "location",
            "label": "Where is the headache located?",
            "type": "single_choice",
            "options": [
                "Forehead / frontal",
                "One side (temple)",
                "Back of head / neck",
                "Behind eyes",
                "All over head",
                "Not sure",
            ],
        },
        {
            "id": "severity",
            "label": "Severity (1 = mild, 10 = severe)",
            "type": "slider",
            "min": 1,
            "max": 10,
            "default": 5,
        },
        {
            "id": "onset",
            "label": "When did it start?",
            "type": "single_choice",
            "options": [
                "A few hours ago",
                "Started today",
                "1 to 3 days ago",
                "More than a week ago",
                "Recurring / chronic",
            ],
        },
        {
            "id": "sensation",
            "label": "How does it feel?",
            "type": "single_choice",
            "options": [
                "Throbbing or pulsing",
                "Dull pressure or aching",
                "Tight band around head",
                "Sharp or stabbing",
            ],
        },
        {
            "id": "associated",
            "label": "Associated symptoms",
            "type": "multi_choice",
            "options": [
                "Sensitivity to light or sound",
                "Nausea",
                "Neck stiffness",
                "Fatigue or drowsiness",
                "None of these",
            ],
        },
    ],
}

RESPIRATORY_ASSESSMENT: dict[str, Any] = {
    "id": "respiratory_intake",
    "title": "Quick Symptom Assessment: Cough & Respiratory",
    "questions": [
        {
            "id": "cough_type",
            "label": "Type of cough",
            "type": "single_choice",
            "options": [
                "Dry / hacking",
                "Wet / bringing up mucus",
                "Tickle in throat",
                "Barking cough",
            ],
        },
        {
            "id": "severity",
            "label": "Disruption level (1 = minor, 10 = severe)",
            "type": "slider",
            "min": 1,
            "max": 10,
            "default": 4,
        },
        {
            "id": "onset",
            "label": "Duration",
            "type": "single_choice",
            "options": [
                "1 to 2 days",
                "3 to 7 days",
                "1 to 3 weeks",
                "Over a month",
            ],
        },
        {
            "id": "associated",
            "label": "Associated symptoms",
            "type": "multi_choice",
            "options": [
                "Fever or chills",
                "Sore throat",
                "Runny or stuffy nose",
                "Mild shortness of breath",
                "Body aches",
                "None of these",
            ],
        },
    ],
}

GENERAL_SYMPTOM_ASSESSMENT: dict[str, Any] = {
    "id": "general_symptom_intake",
    "title": "Quick Symptom Assessment",
    "questions": [
        {
            "id": "location",
            "label": "Primary area of concern",
            "type": "single_choice",
            "options": [
                "Head or neck",
                "Chest or back",
                "Abdomen or stomach",
                "Arms, legs or joints",
                "Skin or rash",
                "Whole body / general",
            ],
        },
        {
            "id": "severity",
            "label": "Severity (1 = mild, 10 = severe)",
            "type": "slider",
            "min": 1,
            "max": 10,
            "default": 5,
        },
        {
            "id": "onset",
            "label": "When did it begin?",
            "type": "single_choice",
            "options": [
                "Started today",
                "Yesterday",
                "A few days ago",
                "More than a week ago",
                "Ongoing / recurring",
            ],
        },
        {
            "id": "sensation",
            "label": "Quality / sensation",
            "type": "single_choice",
            "options": [
                "Sharp or stabbing",
                "Dull ache or soreness",
                "Burning sensation",
                "Cramping or spasm",
                "Throbbing",
                "Other",
            ],
        },
        {
            "id": "associated",
            "label": "Associated symptoms",
            "type": "multi_choice",
            "options": [
                "Fever or chills",
                "Fatigue or weakness",
                "Sleep disruption",
                "Nausea",
                "None of these",
            ],
        },
    ],
}


# Trigger patterns
_STOMACH_PATTERN = re.compile(
    r"\b(stomach|abdomen|abdominal|belly|tummy|gut|digestive|cramp|cramps|cramping|diarrhea|constipat|nausea)\b",
    re.IGNORECASE,
)
_HEADACHE_PATTERN = re.compile(
    r"\b(headache|headaches|migraine|migraines|head pain|temple|throbbing head)\b",
    re.IGNORECASE,
)
_RESPIRATORY_PATTERN = re.compile(
    r"\b(cough|coughing|sore throat|congestion|phlegm|mucus|bronchitis|wheez)\b",
    re.IGNORECASE,
)
_GENERAL_SYMPTOM_PATTERN = re.compile(
    r"\b(pain|hurts?|aching|sore|fever|swollen|swelling|rash|dizzy|dizziness|fatigue|numbness|stiff)\b",
    re.IGNORECASE,
)

# General medical education indicator (should NOT trigger an assessment questionnaire)
_EDU_PATTERN = re.compile(
    r"^(what (is|are)|how (does|do)|why (is|do|does)|explain|tell me about|can you explain"
    r"|what causes|what means|benefits of|difference between|how to prevent)\b",
    re.IGNORECASE,
)

# User asking for next steps, remedies, interim summary, or to stop questioning
_GUIDANCE_OR_STOP_PATTERN = re.compile(
    r"\b(how (do|can) i (fix|treat|stop|cure|help|manage)|what (should|can) i (do|take)|what to do"
    r"|stop (asking|questions)|just tell me|can you summarize|give me a summary|what could it be)\b",
    re.IGNORECASE,
)


def get_assessment_for_input(
    user_message: str,
    history: list[dict] | None = None,
    topic: str | None = None,
) -> dict[str, Any] | None:
    """Return a validated AssessmentForm dict if the message is a personal symptom intake.

    Returns None if:
    - Emergency is detected
    - The query is general medical education
    - The user already completed an assessment questionnaire in this conversation
    - The user asks for a summary, guidance, or to stop questioning
    - The message is off-topic or a pure greeting
    """
    stripped = user_message.strip()

    # Emergencies must NEVER display routine assessment forms
    if assess_input(stripped).category == "emergency":
        return None

    # Check if user requested guidance, summary, or stopping assessment
    if _GUIDANCE_OR_STOP_PATTERN.search(stripped):
        return None

    # Check if the user already submitted a structured assessment in prior turns
    if history:
        for turn in reversed(history):
            if turn.get("role") == "user":
                content = turn.get("content", "")
                if ("Location:" in content and "Severity:" in content) or (
                    ("Severity:" in content or "/10" in content)
                    and (
                        "Location:" in content
                        or "Onset" in content
                        or "Associated" in content
                        or "pain located:" in content.lower()
                        or "type of cough:" in content.lower()
                        or "area of concern:" in content.lower()
                    )
                ):
                    # User already completed the assessment; do not repeat it
                    return None

    # General medical education questions should not show an intake form
    if _EDU_PATTERN.search(stripped) and not ("my" in stripped.lower() or "i have" in stripped.lower()):
        return None

    # Match symptom category
    if _STOMACH_PATTERN.search(stripped) or topic == "Digestive Health":
        return STOMACH_ASSESSMENT

    if _HEADACHE_PATTERN.search(stripped) or topic == "Headache":
        return HEADACHE_ASSESSMENT

    if _RESPIRATORY_PATTERN.search(stripped) or topic == "Respiratory":
        return RESPIRATORY_ASSESSMENT

    if _GENERAL_SYMPTOM_PATTERN.search(stripped):
        return GENERAL_SYMPTOM_ASSESSMENT

    return None
