"""
Structured clinical assessment definitions and generation for MediGuide AI v2.0.

Provides validated, structured question templates for common symptom categories
so users can easily provide clinical intake context via one-question-at-a-time
interactive selection controls with progress indicators and adaptive follow-up.
"""

from __future__ import annotations

import re
from typing import Any

from .safety import assess_input

# ---------------------------------------------------------------------------
# Assessment Question Banks
# ---------------------------------------------------------------------------

STOMACH_ASSESSMENT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "location",
        "label": "Where are you experiencing the pain?",
        "question": "Where are you experiencing the pain?",
        "explanation": "Pinpointing the specific region helps differentiate between stomach, intestinal, gallbladder, or muscular causes.",
        "category": "Stomach & Abdomen",
        "type": "single_choice",
        "options": [
            "Upper abdomen",
            "Lower abdomen",
            "Left side",
            "Right side",
            "Around the belly button",
            "Around belly button",
            "Entire abdomen",
            "Across the abdomen",
            "Not sure",
            "Other",
        ],
        "step_number": 1,
        "total_steps": 5,
    },
    {
        "id": "sensation",
        "label": "How would you describe the pain?",
        "question": "How would you describe the pain?",
        "explanation": "The sensation (sharp, cramping, dull) helps identify whether the cause is more likely inflammatory, spasmodic, or functional.",
        "category": "Stomach & Abdomen",
        "type": "single_choice",
        "options": [
            "Sharp",
            "Dull ache",
            "Cramping",
            "Burning",
            "Stabbing",
            "Throbbing",
            "Not sure",
            "Other",
        ],
        "step_number": 2,
        "total_steps": 5,
    },
    {
        "id": "onset",
        "label": "When did the pain begin?",
        "question": "When did the pain begin?",
        "explanation": "The onset timeline helps distinguish acute conditions needing prompt care from gradual or recurring patterns.",
        "category": "Stomach & Abdomen",
        "type": "single_choice",
        "options": [
            "Just started (within hours)",
            "Started today",
            "Yesterday",
            "A few days ago",
            "More than a week ago",
            "Not sure",
        ],
        "step_number": 3,
        "total_steps": 5,
    },
    {
        "id": "severity",
        "label": "How severe is the pain?",
        "question": "How severe is the pain?",
        "explanation": "Rate the pain intensity from 1 (very mild) to 10 (severe / unbearable) to gauge disruption and urgency.",
        "category": "Stomach & Abdomen",
        "type": "slider",
        "min": 1,
        "max": 10,
        "default": 5,
        "step_number": 4,
        "total_steps": 5,
    },
    {
        "id": "associated",
        "label": "Are you experiencing any other symptoms?",
        "question": "Are you experiencing any other symptoms?",
        "explanation": "Co-occurring digestive or systemic symptoms give a complete picture of your overall condition.",
        "category": "Stomach & Abdomen",
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
        "step_number": 5,
        "total_steps": 5,
    },
]

HEADACHE_ASSESSMENT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "location",
        "label": "Where is the headache located?",
        "question": "Where is the headache located?",
        "explanation": "The anatomical region helps distinguish between tension, migraine, sinus, or cluster headaches.",
        "category": "Headache",
        "type": "single_choice",
        "options": [
            "Forehead / frontal",
            "One side (temple)",
            "Back of head / neck",
            "Behind eyes",
            "All over head",
            "Not sure",
            "Other",
        ],
        "step_number": 1,
        "total_steps": 5,
    },
    {
        "id": "sensation",
        "label": "How does it feel?",
        "question": "How does it feel?",
        "explanation": "Pulsing often points to vascular or migraine patterns, whereas a tight band suggests tension.",
        "category": "Headache",
        "type": "single_choice",
        "options": [
            "Throbbing or pulsing",
            "Dull pressure or aching",
            "Tight band around head",
            "Sharp or stabbing",
            "Not sure",
            "Other",
        ],
        "step_number": 2,
        "total_steps": 5,
    },
    {
        "id": "onset",
        "label": "When did it start?",
        "question": "When did it start?",
        "explanation": "Knowing the duration helps evaluate whether it is an acute episode or a persistent headache.",
        "category": "Headache",
        "type": "single_choice",
        "options": [
            "A few hours ago",
            "Started today",
            "1 to 3 days ago",
            "More than a week ago",
            "Recurring / chronic",
            "Not sure",
        ],
        "step_number": 3,
        "total_steps": 5,
    },
    {
        "id": "severity",
        "label": "Severity (1 = mild, 10 = severe)",
        "question": "Severity (1 = mild, 10 = severe)",
        "explanation": "Headache intensity helps assess required rest, comfort measures, or when professional evaluation is needed.",
        "category": "Headache",
        "type": "slider",
        "min": 1,
        "max": 10,
        "default": 5,
        "step_number": 4,
        "total_steps": 5,
    },
    {
        "id": "associated",
        "label": "Associated symptoms",
        "question": "Associated symptoms (select all that apply)",
        "explanation": "Associated neurological or systemic signs are key diagnostic indicators.",
        "category": "Headache",
        "type": "multi_choice",
        "options": [
            "Sensitivity to light or sound",
            "Nausea",
            "Neck stiffness",
            "Fatigue or drowsiness",
            "None of these",
            "Other",
        ],
        "step_number": 5,
        "total_steps": 5,
    },
]

RESPIRATORY_ASSESSMENT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "cough_type",
        "label": "Type of cough",
        "question": "What type of cough are you experiencing?",
        "explanation": "Productive (wet) vs. dry coughs indicate different airway responses.",
        "category": "Cough & Respiratory",
        "type": "single_choice",
        "options": [
            "Dry / hacking",
            "Wet / bringing up mucus",
            "Tickle in throat",
            "Barking cough",
            "Not sure",
            "Other",
        ],
        "step_number": 1,
        "total_steps": 4,
    },
    {
        "id": "onset",
        "label": "Duration",
        "question": "How long have you had this cough?",
        "explanation": "Duration indicates acute infection versus subacute or chronic airway irritation.",
        "category": "Cough & Respiratory",
        "type": "single_choice",
        "options": [
            "1 to 2 days",
            "3 to 7 days",
            "1 to 3 weeks",
            "Over a month",
            "Not sure",
        ],
        "step_number": 2,
        "total_steps": 4,
    },
    {
        "id": "severity",
        "label": "Disruption level (1 = minor, 10 = severe)",
        "question": "Disruption level (1 = minor, 10 = severe)",
        "explanation": "How much the cough interferes with sleep, talking, and daily activity.",
        "category": "Cough & Respiratory",
        "type": "slider",
        "min": 1,
        "max": 10,
        "default": 4,
        "step_number": 3,
        "total_steps": 4,
    },
    {
        "id": "associated",
        "label": "Associated symptoms",
        "question": "Associated symptoms (select all that apply)",
        "explanation": "Systemic symptoms like fever or chills clarify infectious and respiratory causes.",
        "category": "Cough & Respiratory",
        "type": "multi_choice",
        "options": [
            "Fever or chills",
            "Sore throat",
            "Runny or stuffy nose",
            "Mild shortness of breath",
            "Body aches",
            "None of these",
            "Other",
        ],
        "step_number": 4,
        "total_steps": 4,
    },
]

GENERAL_ASSESSMENT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "location",
        "label": "Primary area of concern",
        "question": "Where is the primary area of concern?",
        "explanation": "Identifying the affected bodily region grounds the clinical inquiry.",
        "category": "General Symptoms",
        "type": "single_choice",
        "options": [
            "Head or neck",
            "Chest or back",
            "Abdomen or stomach",
            "Arms, legs or joints",
            "Skin or rash",
            "Whole body / general",
            "Other",
        ],
        "step_number": 1,
        "total_steps": 5,
    },
    {
        "id": "sensation",
        "label": "Quality / sensation",
        "question": "How would you describe the sensation?",
        "explanation": "Describing the character of discomfort clarifies possible underlying mechanisms.",
        "category": "General Symptoms",
        "type": "single_choice",
        "options": [
            "Sharp or stabbing",
            "Dull ache or soreness",
            "Burning sensation",
            "Cramping or spasm",
            "Throbbing",
            "Not sure",
            "Other",
        ],
        "step_number": 2,
        "total_steps": 5,
    },
    {
        "id": "onset",
        "label": "When did it begin?",
        "question": "When did it begin?",
        "explanation": "Timing provides essential context for evaluating symptom progression.",
        "category": "General Symptoms",
        "type": "single_choice",
        "options": [
            "Started today",
            "Yesterday",
            "A few days ago",
            "More than a week ago",
            "Ongoing / recurring",
            "Not sure",
        ],
        "step_number": 3,
        "total_steps": 5,
    },
    {
        "id": "severity",
        "label": "Severity (1 = mild, 10 = severe)",
        "question": "Severity (1 = mild, 10 = severe)",
        "explanation": "Rating discomfort from 1 to 10 helps understand the severity and functional impact.",
        "category": "General Symptoms",
        "type": "slider",
        "min": 1,
        "max": 10,
        "default": 5,
        "step_number": 4,
        "total_steps": 5,
    },
    {
        "id": "associated",
        "label": "Associated symptoms",
        "question": "Associated symptoms (select all that apply)",
        "explanation": "Other concurrent symptoms help identify related systemic patterns.",
        "category": "General Symptoms",
        "type": "multi_choice",
        "options": [
            "Fever or chills",
            "Fatigue or weakness",
            "Sleep disruption",
            "Nausea",
            "None of these",
            "Other",
        ],
        "step_number": 5,
        "total_steps": 5,
    },
]

# Legacy dictionary format mapping for backward-compatible tests
STOMACH_ASSESSMENT: dict[str, Any] = {
    "id": "stomach_pain_intake",
    "title": "Quick Symptom Assessment: Stomach & Abdomen",
    "questions": STOMACH_ASSESSMENT_QUESTIONS,
}

HEADACHE_ASSESSMENT: dict[str, Any] = {
    "id": "headache_intake",
    "title": "Quick Symptom Assessment: Headache",
    "questions": HEADACHE_ASSESSMENT_QUESTIONS,
}

RESPIRATORY_ASSESSMENT: dict[str, Any] = {
    "id": "respiratory_intake",
    "title": "Quick Symptom Assessment: Cough & Respiratory",
    "questions": RESPIRATORY_ASSESSMENT_QUESTIONS,
}

GENERAL_SYMPTOM_ASSESSMENT: dict[str, Any] = {
    "id": "general_symptom_intake",
    "title": "Quick Symptom Assessment",
    "questions": GENERAL_ASSESSMENT_QUESTIONS,
}


# ---------------------------------------------------------------------------
# Trigger & Intent Patterns
# ---------------------------------------------------------------------------

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

_EDU_PATTERN = re.compile(
    r"^(what (is|are)|how (does|do)|why (is|do|does)|explain|tell me about|can you explain"
    r"|what causes|what means|benefits of|difference between|how to prevent)\b",
    re.IGNORECASE,
)

_STOP_OR_GUIDANCE_PATTERN = re.compile(
    r"\b(stop (asking|questions)|just tell me|can you summarize|give me a summary|what could it be"
    r"|how (do|can) i (fix|treat|stop|cure|help|manage)|what (should|can) i (do|take)|what to do)\b",
    re.IGNORECASE,
)


def _get_category_questions(user_message: str, topic: str | None = None) -> tuple[str, list[dict[str, Any]], dict[str, Any]] | None:
    """Return category name, questions list, and full assessment template for message."""
    stripped = user_message.strip()
    if _STOMACH_PATTERN.search(stripped) or topic == "Digestive Health":
        return "Stomach & Abdomen", STOMACH_ASSESSMENT_QUESTIONS, STOMACH_ASSESSMENT
    if _HEADACHE_PATTERN.search(stripped) or topic == "Headache":
        return "Headache", HEADACHE_ASSESSMENT_QUESTIONS, HEADACHE_ASSESSMENT
    if _RESPIRATORY_PATTERN.search(stripped) or topic == "Respiratory":
        return "Cough & Respiratory", RESPIRATORY_ASSESSMENT_QUESTIONS, RESPIRATORY_ASSESSMENT
    if _GENERAL_SYMPTOM_PATTERN.search(stripped):
        return "General Symptoms", GENERAL_ASSESSMENT_QUESTIONS, GENERAL_SYMPTOM_ASSESSMENT
    return None


def _extract_answered_dimensions(history: list[dict] | None, latest_message: str) -> set[str]:
    """Inspect history and latest message to find which assessment dimensions have been answered."""
    answered: set[str] = set()
    all_user_text: list[str] = []

    if history:
        for turn in history:
            if turn.get("role") == "user":
                all_user_text.append(turn.get("content", ""))
    all_user_text.append(latest_message)
    combined = "\n".join(all_user_text).lower()

    # Location check
    if any(k in combined for k in [
        "location:", "upper abdomen", "lower abdomen", "left side", "right side",
        "around belly", "belly button", "entire abdomen", "forehead", "temple",
        "behind eyes", "back of head", "neck", "chest", "joints"
    ]):
        answered.add("location")

    # Sensation check
    if any(k in combined for k in [
        "sensation:", "sharp", "dull", "cramping", "burning", "stabbing",
        "throbbing", "tight band", "aching", "type of cough:", "dry", "wet"
    ]):
        answered.add("sensation")
        answered.add("cough_type")

    # Onset / Duration check
    if any(k in combined for k in [
        "onset:", "duration:", "yesterday", "started today", "just started",
        "days ago", "week ago", "weeks ago", "hours ago", "recurring", "chronic"
    ]):
        answered.add("onset")

    # Severity check
    if any(k in combined for k in [
        "severity:", "/10", "out of 10", "1 to 10", "mild", "moderate", "severe"
    ]):
        answered.add("severity")

    # Associated symptoms check
    if any(k in combined for k in [
        "associated:", "associated symptoms:", "nausea", "vomiting", "fever",
        "bloating", "diarrhoea", "constipation", "none of these"
    ]):
        answered.add("associated")

    return answered


# ---------------------------------------------------------------------------
# Public Assessment Helpers
# ---------------------------------------------------------------------------

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

    if assess_input(stripped).category == "emergency":
        return None

    if _STOP_OR_GUIDANCE_PATTERN.search(stripped):
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
                    return None

    if _EDU_PATTERN.search(stripped) and not ("my" in stripped.lower() or "i have" in stripped.lower()):
        return None

    matched = _get_category_questions(user_message, topic)
    if matched:
        _, _, assessment_template = matched
        return assessment_template

    return None


def get_interactive_assessment_step(
    user_message: str,
    history: list[dict] | None = None,
    topic: str | None = None,
) -> dict[str, Any] | None:
    """Determine the next one-at-a-time assessment question or summary.

    Returns a dict with:
    - response_type: "assessment_question" | "assessment_summary" | None
    - active_question: dict containing the single next question with progress
    - assessment: the full category assessment template (for client coordination)
    - summary: structured summary if all questions are completed
    """
    stripped = user_message.strip()

    if assess_input(stripped).category == "emergency":
        return None

    if _EDU_PATTERN.search(stripped) and not ("my" in stripped.lower() or "i have" in stripped.lower()):
        return None

    matched = _get_category_questions(user_message, topic)
    if not matched:
        # Check if history has an ongoing category
        if history:
            for turn in history:
                text = turn.get("content", "")
                m = _get_category_questions(text)
                if m:
                    matched = m
                    break
    if not matched:
        return None

    category_name, questions, assessment_template = matched
    answered = _extract_answered_dimensions(history, stripped)

    # Check if user requested summary or guidance early
    wants_summary = bool(_STOP_OR_GUIDANCE_PATTERN.search(stripped))

    # Check if a completed multi-field assessment block was submitted in this turn or prior turn
    all_user_text: list[str] = [stripped]
    if history:
        for turn in history:
            if turn.get("role") == "user":
                all_user_text.append(turn.get("content", ""))

    has_completed_intake_block = any(
        ("Location:" in txt and "Severity:" in txt) or
        ("location:" in txt.lower() and "/10" in txt)
        for txt in all_user_text
    )

    # Find unanswered questions in this sequence
    unanswered_questions = [q for q in questions if q["id"] not in answered]

    # If all answered, or completed intake block submitted, or user wants summary -> Generate Assessment Summary
    if not unanswered_questions or has_completed_intake_block or wants_summary:
        summary_data = generate_assessment_summary_data(history, stripped, category_name)
        return {
            "response_type": "assessment_summary",
            "summary": summary_data,
            "assessment": None,
            "category": category_name,
        }

    # Otherwise return the NEXT question in order
    next_q = unanswered_questions[0]
    current_index = questions.index(next_q) + 1
    total_count = len(questions)

    question_copy = dict(next_q)
    question_copy["step_number"] = current_index
    question_copy["total_steps"] = total_count

    return {
        "response_type": "assessment_question",
        "active_question": question_copy,
        "assessment": assessment_template,
        "category": category_name,
    }


def generate_assessment_summary_data(
    history: list[dict] | None,
    latest_message: str,
    category: str = "Symptom Assessment",
) -> dict[str, Any]:
    """Synthesize reported answers from conversation turns into a structured summary."""
    all_user_lines: list[str] = []
    if history:
        for turn in history:
            if turn.get("role") == "user":
                all_user_lines.extend(turn.get("content", "").split("\n"))
    all_user_lines.extend(latest_message.split("\n"))

    reported: list[dict[str, str]] = []
    seen_labels: set[str] = set()

    label_keywords = [
        ("Location", ["location:", "area of concern:"]),
        ("Sensation", ["sensation:", "type of cough:"]),
        ("Onset & Duration", ["onset:", "duration:"]),
        ("Severity", ["severity:", "/10"]),
        ("Associated Symptoms", ["associated:", "associated symptoms:"]),
        ("Additional Notes", ["additional details:", "notes:"]),
    ]

    for line in all_user_lines:
        trimmed = line.strip()
        if not trimmed:
            continue
        for display_label, prefixes in label_keywords:
            if display_label not in seen_labels and any(p in trimmed.lower() for p in prefixes):
                parts = trimmed.split(":", 1)
                val = parts[1].strip() if len(parts) > 1 else trimmed
                reported.append({"label": display_label, "value": val})
                seen_labels.add(display_label)
                break

    # If few structured lines were parsed, synthesize from text
    if not reported:
        reported.append({"label": "Reported Concern", "value": latest_message[:120]})

    # Category-specific guidance
    if "stomach" in category.lower() or "abdomen" in category.lower():
        possible_explanations = [
            "Digestive tract irritation, gastritis, or dietary intolerance",
            "Functional cramping, gas buildup, or temporary indigestion",
            "Musculoskeletal strain across abdominal wall muscles",
        ]
        warning_signs = [
            "Sudden, excruciating, or rapidly worsening pain",
            "High fever, persistent vomiting, or inability to retain fluids",
            "Blood in vomit or dark, tarry stools",
            "Rigid, board-like abdomen or severe pain when releasing pressure",
        ]
        safe_measures = [
            "Rest comfortably in a reclined or side-lying position",
            "Sip clear fluids (water, oral rehydration, or diluted broth) gradually",
            "Avoid NSAIDs (such as ibuprofen or aspirin) and laxatives without physician advice",
        ]
    elif "headache" in category.lower():
        possible_explanations = [
            "Tension headache related to stress, screen fatigue, or posture",
            "Migraine or vascular headache pattern with sensory sensitivity",
            "Dehydration or disrupted sleep schedule",
        ]
        warning_signs = [
            "Sudden severe headache reaching peak within seconds (thunderclap)",
            "Stiff neck, confusion, fever, or rash",
            "New weakness, numbness, difficulty speaking, or vision loss",
        ]
        safe_measures = [
            "Rest in a quiet, darkened room",
            "Apply a cool or warm compress to forehead or neck",
            "Stay hydrated with small, regular sips of water",
        ]
    else:
        possible_explanations = [
            "Common viral upper respiratory irritation or acute inflammation",
            "Localized musculoskeletal strain or benign functional discomfort",
            "Environmental or seasonal allergen sensitivity",
        ]
        warning_signs = [
            "Difficulty breathing, chest tightness, or blueness around lips",
            "Persistent high fever not responding to supportive measures",
            "Confusion, lethargy, or inability to drink liquids",
        ]
        safe_measures = [
            "Prioritize physical rest and avoid strenuous exertion",
            "Maintain steady hydration with room-temperature fluids",
            "Monitor symptoms closely for progression over the next 24 to 48 hours",
        ]

    return {
        "category": category,
        "reported_symptoms": reported,
        "possible_explanations": possible_explanations,
        "warning_signs": warning_signs,
        "safe_measures": safe_measures,
        "professional_care_recommendation": (
            "Because MediGuide is an educational assistant and cannot perform an in-person physical examination, "
            "please consult a licensed healthcare professional for an accurate diagnosis and individualized care plan."
        ),
    }
