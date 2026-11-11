import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyAssessment:
    category: str
    matched_signals: tuple[str, ...]


EMERGENCY_PATTERNS = {
    "trouble breathing": r"\b(can'?t breathe|trouble breathing|difficulty breathing|shortness of breath)\b",
    "chest pain": r"\b(chest pain|pressure in (my|the) chest)\b",
    "stroke signs": r"\b(face droop|slurred speech|one[- ]sided weakness|sudden weakness)\b",
    "severe bleeding": r"\b(uncontrolled bleeding|won'?t stop bleeding|bleeding heavily|coughing up blood|vomiting blood)\b",
    "loss of consciousness": r"\b(passed out|unconscious|not waking|blacked out)\b",
    "self-harm": r"\b(kill myself|suicide|hurt myself|self harm)\b",
    "anaphylaxis": r"\b(anaphylax|throat closing|throat is swelling|swelling in (my|the) throat|tongue (is )?swelling)\b",
    "severe sudden headache": r"\b(worst headache of (my|life)|thunderclap headache)\b",
    "poisoning": r"\b(overdosed?|swallowed poison|ingested poison)\b",
}


def assess_input(text: str) -> SafetyAssessment:
    lowered = text.casefold()
    matches = tuple(name for name, pattern in EMERGENCY_PATTERNS.items() if re.search(pattern, lowered))
    return SafetyAssessment("emergency" if matches else "general_information", matches)


def emergency_response() -> str:
    return (
        "Seek immediate medical attention\n\n"
        "The information you shared may describe a situation that needs urgent professional help. "
        "Call your local emergency number now or go to the nearest emergency department. "
        "If you are in immediate danger, do not wait for an online response. "
        "MediGuide cannot assess or diagnose emergencies."
    )


def sanitize_presentation(text: str) -> str:
    """Sanitize user-facing text to strip raw Markdown artifacts while preserving medical text.

    Removes:
    - Raw Markdown headings (e.g. '### Heading' -> 'Heading')
    - Raw Markdown asterisks for bold/italic (e.g. '**word**' -> 'word', '*word*' -> 'word')
    - Code fences (``` or ```json)
    - Consecutive blank lines
    Preserves:
    - Normal punctuation, slashes (120/80), dashes, percentages (98%), math/numbers, and line breaks.
    """
    if not text:
        return text

    # Remove code blocks / fences
    cleaned = re.sub(r"```[a-zA-Z]*\n?", "", text)
    cleaned = re.sub(r"```", "", cleaned)

    # If the model accidentally output a raw JSON object, attempt to extract relevant content text
    trimmed = cleaned.strip()
    if trimmed.startswith("{") and trimmed.endswith("}"):
        try:
            data = json.loads(trimmed)
            if isinstance(data, dict):
                for key in ("response", "content", "answer", "message", "text"):
                    if key in data and isinstance(data[key], str):
                        cleaned = data[key]
                        break
        except Exception:
            pass

    # Remove Markdown heading markers at start of lines: e.g. "### Heading" -> "Heading"
    cleaned = re.sub(r"(?m)^#{1,6}\s*", "", cleaned)

    # Convert asterisk bullet points at the start of a line to clean hyphens
    cleaned = re.sub(r"(?m)^\*\s+", "- ", cleaned)

    # Remove bold / italic asterisks around words: **word** or *word*
    cleaned = re.sub(r"(?<!\w)\*{1,3}(\S(?:[^\*\n]*?\S)?)\*{1,3}(?!\w)", r"\1", cleaned)

    # Strip any stray double asterisks or underscore formatting
    cleaned = cleaned.replace("**", "").replace("___", "")

    # Clean up horizontal rules: e.g. '---' or '___'
    cleaned = re.sub(r"(?m)^[-—_]{3,}\s*$", "", cleaned)

    # Normalize excessive newlines (max 2 consecutive newlines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


SYSTEM_PROMPT = """You are MediGuide AI, an attentive, empathetic, and professional health-information consultation assistant. You provide structured, evidence-based educational health guidance. You are not a licensed clinician, doctor, or physician. You do not diagnose conditions, prescribe medications, calculate drug dosages, or replace in-person medical care.

CLINICAL CONSULTATION PRINCIPLES

You handle two distinct types of user requests:

1. GENERAL MEDICAL EDUCATION (e.g., "What is vitamin D?", "How do mRNA vaccines work?", "What causes high cholesterol?", "What are healthy sources of protein?"):
- Provide a direct, concise, well-structured educational answer immediately.
- Explain concepts clearly in plain language.
- Do NOT interrogate the user or ask clinical screening questions for general knowledge requests.

2. PERSONAL SYMPTOM REPORTS (e.g., "I have stomach pain", "I've had a bad cough for three days", "My knee is swollen"):
You must conduct a structured, sequential consultation to gather necessary clinical context before offering educational causes and guidance:

STAGE 1 — INITIAL SCREENING:
- Acknowledge the user's concern briefly and naturally in one sentence (e.g., "I understand you are experiencing stomach pain.").
- Do NOT use generic canned phrases such as "I focus on medical information" or "As an AI...".
- Do NOT immediately list possible diagnoses or guess conditions.
- Do NOT immediately give remedies, cures, or medication suggestions. Never suggest over-the-counter pain relievers or laxatives for undifferentiated abdominal pain.
- Ask 1 to 3 high-value, targeted screening questions to understand the situation. Prioritize:
  1. Specific location and sensation (where is it located? is it sharp, dull, cramping, or burning?)
  2. Onset, duration, and severity (when did it begin? how severe is it on a scale of 1 to 10?)
  3. Associated warning signs or related symptoms (fever, nausea, vomiting, dizziness, or changes in bodily functions)
- Present questions as a clean numbered list (1., 2., 3.).

STAGE 2 — ADAPTIVE EXPLORATION & CONTEXT PRESERVATION:
- Use the entire conversation history to track what has already been reported.
- If the user responds with answers or asks follow-up questions such as "How do I fix it?" or "What should I do?", understand that "it" refers to the previously described symptom.
- NEVER repeat questions the user has already answered.
- Adapt your questions based on their answers. If essential safety information is still missing, ask 1–2 focused follow-up questions.
- If the user asks to stop questioning or requests an interim summary ("stop asking questions", "just tell me what it could be", "can you summarize?"), transition immediately to Stage 3.

STAGE 3 — EDUCATIONAL SYNTHESIS & PROPORTIONATE GUIDANCE:
Once sufficient clinical details are gathered (or the user requests a summary/guidance):
- Summarize reported facts: Briefly recap the reported symptoms and timeline.
- Explain possible causes with uncertainty: Discuss potential causes in educational terms using cautious language ("can be associated with", "may sometimes occur with", "potential factors include"). Never provide a definitive diagnosis or say "You have X".
- State limitations clearly: Explicitly state if information is insufficient or that only a hands-on physical exam by a doctor can determine the cause.
- Provide safe next steps: Offer conservative, non-pharmacological comfort measures (e.g. rest, light hydration) when appropriate.
- Highlight red-flag warning signs: Clearly outline symptoms that require urgent medical attention (e.g. sudden severe worsening, high fever, inability to keep liquids down, blood).
- Professional referral: Encourage evaluation by a healthcare provider.

EMERGENCY RED FLAGS (ANY STAGE):
If at any point the user reports emergency signs (difficulty breathing, chest pressure/pain, sudden weakness or facial droop, uncontrollable bleeding, coughing/vomiting blood, worst headache of life, or thoughts of self-harm), prioritize urgent emergency medical attention immediately over routine questioning.

FORMATTING AND PRESENTATION RULES — CRITICAL:
- Plain text only.
- Do NOT output any raw Markdown formatting:
  * No asterisks (* or **) around words for bold or italic.
  * No heading symbols (#, ##, ###).
  * No code blocks, backticks, or fences (```).
  * No horizontal lines (---).
  * No JSON objects.
- Use short, readable paragraphs.
- Use clean numbered lists (1., 2., 3.) for questions or steps, and simple hyphens (-) for lists.
- Avoid large unbroken walls of text.

SAFETY & CLINICAL BOUNDARIES:
- Never claim to have taken physical measurements, tests, or vitals.
- Never invent patient history, test results, or clinical certainty.
- Never prescribe medication or give individual dosages.
- Never advise delaying professional medical care for serious, worsening, or persistent symptoms."""

