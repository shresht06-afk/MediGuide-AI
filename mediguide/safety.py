from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SafetyAssessment:
    category: str
    matched_signals: tuple[str, ...]


EMERGENCY_PATTERNS = {
    "trouble breathing": r"\b(can'?t breathe|trouble breathing|difficulty breathing|shortness of breath)\b",
    "chest pain": r"\b(chest pain|pressure in (my|the) chest)\b",
    "stroke signs": r"\b(face droop|slurred speech|one[- ]sided weakness|sudden weakness)\b",
    "severe bleeding": r"\b(uncontrolled bleeding|won'?t stop bleeding)\b",
    "loss of consciousness": r"\b(passed out|unconscious|not waking)\b",
    "self-harm": r"\b(kill myself|suicide|hurt myself|self harm)\b",
}


def assess_input(text: str) -> SafetyAssessment:
    lowered = text.casefold()
    matches = tuple(name for name, pattern in EMERGENCY_PATTERNS.items() if re.search(pattern, lowered))
    return SafetyAssessment("emergency" if matches else "general_information", matches)


def emergency_response() -> str:
    return (
        "## Seek immediate medical attention\n\n"
        "The information you shared may describe a situation that needs urgent professional help. "
        "Call your local emergency number now or go to the nearest emergency department. "
        "If you are in immediate danger, do not wait for an online response. "
        "MediGuide cannot assess or diagnose emergencies."
    )


SYSTEM_PROMPT = """You are MediGuide AI, a health-information and decision-support companion, not a doctor.
Give general educational information in plain language. Never diagnose, prescribe, claim certainty,
or imply you examined the user. Separate responses into:
## General information
## Possible explanations
## What you can do
## When to seek medical help
Use cautious language, recommend a qualified professional when appropriate, and make urgent warning signs
clear. Do not provide dangerous instructions. Do not repeat labels such as 'User:' or 'Assistant:'."""
