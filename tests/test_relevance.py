"""
Tests for the medical relevance filter and its integration with MediGuide AI.

Test categories (all offline — no OpenRouter calls required):
  1. MEDICAL    — questions that must always reach the LLM.
  2. UNRELATED  — clearly off-topic requests that must be declined.
  3. AMBIGUOUS  — borderline inputs that must be passed through (fail-open).
  4. EMERGENCY  — safety-critical inputs that must bypass the relevance filter.
  5. FOLLOWUP   — contextual follow-ups in a medical conversation.

Run with:
    python -m pytest tests/test_relevance.py -v
"""

from __future__ import annotations

import sys
import os

# Ensure the project root is on the path regardless of working directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from mediguide.relevance import (
    OFF_TOPIC_RESPONSE,
    RelevanceResult,
    _score,
    check_relevance,
)
from mediguide.safety import assess_input


# ===========================================================================
# Helpers
# ===========================================================================


def _medical_history() -> list[dict]:
    """Return a minimal conversation history whose last assistant turn has
    clear medical content, used for follow-up tests."""
    return [
        {"role": "user", "content": "I have been having chest tightness and shortness of breath."},
        {
            "role": "assistant",
            "content": (
                "Chest tightness combined with shortness of breath can be associated "
                "with several conditions ranging from anxiety and asthma to cardiac issues. "
                "If the symptoms are severe or sudden, seek medical attention promptly."
            ),
        },
    ]


def _nonmedical_history() -> list[dict]:
    """Return a history whose last assistant turn has no medical content."""
    return [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
    ]


# ===========================================================================
# 1. MEDICAL questions — must always be accepted (is_medical=True)
# ===========================================================================


MEDICAL_INPUTS = [
    # Symptoms
    "I have had a persistent headache for three days.",
    "My child has a fever of 39 degrees. What should I do?",
    "I feel dizzy and nauseous after eating.",
    "I've been experiencing lower back pain for a week.",
    "There is a rash on my arm that is itchy and red.",
    # Conditions
    "Can you explain what type 2 diabetes means?",
    "What are the early signs of hypertension?",
    "How is asthma typically managed in adults?",
    "What does a migraine feel like compared to a tension headache?",
    "I was recently diagnosed with anemia. What should I eat?",
    # Medications
    "Is it safe to take ibuprofen every day for joint pain?",
    "What is the difference between paracetamol and aspirin?",
    "How does an antibiotic work in the body?",
    "Can I take a vitamin D supplement with my blood pressure medication?",
    # Nutrition and wellness
    "How much protein do I need daily if I exercise regularly?",
    "What foods are good for gut health and digestion?",
    "Does poor sleep affect the immune system?",
    "What are healthy stress management techniques?",
    # Mental health
    "I have been feeling very anxious lately. What can help?",
    "How do I know if I have depression?",
    # First aid
    "How do I treat a minor burn at home?",
    "What is the correct way to perform CPR?",
    # Preventive health
    "At what age should I get a cholesterol screening?",
    "What vaccines are recommended for adults over 50?",
    # Reproductive / life-stage
    "What symptoms are common in early pregnancy?",
    "How does menopause affect sleep?",
    # Medical professionals
    "Should I see a cardiologist for palpitations?",
    "What does a dermatologist do for acne?",
]


@pytest.mark.parametrize("message", MEDICAL_INPUTS)
def test_medical_questions_are_accepted(message: str) -> None:
    result = check_relevance(message)
    assert result.is_medical is True, (
        f"Expected is_medical=True for medical question but got False.\n"
        f"  Message : {message!r}\n"
        f"  Score   : {result.score}\n"
        f"  Reason  : {result.reason}"
    )


# ===========================================================================
# 2. UNRELATED requests — must be declined (is_medical=False)
# ===========================================================================


UNRELATED_INPUTS = [
    # Programming / software
    "Write a Python function to reverse a string.",
    "How do I fix a SQL database query that is running slowly?",
    "Explain the difference between React and Vue frameworks.",
    "What is a Docker container and how do I deploy one?",
    "Can you debug this JavaScript code for me?",
    # Mathematics
    "Solve the quadratic equation x squared plus 5x plus 6 equals 0.",
    "What is the derivative of x cubed?",
    "Explain the Pythagorean theorem.",
    # Geography / history / trivia
    "What is the capital city of Australia?",
    "Which country has the longest river in the world?",
    "What year did World War II end?",
    # Entertainment
    "Who won the best actor award at the Oscars last year?",
    "What is the highest-grossing movie of all time?",
    "Recommend a good Netflix series to watch this weekend.",
    # Finance
    "What is the current bitcoin price?",
    "Should I invest in index funds or individual stocks?",
    # Non-health writing tasks
    "Write me an essay about climate change.",
    "Translate this sentence into French.",
]


@pytest.mark.parametrize("message", UNRELATED_INPUTS)
def test_unrelated_requests_are_declined(message: str) -> None:
    result = check_relevance(message)
    assert result.is_medical is False, (
        f"Expected is_medical=False for unrelated request but got True.\n"
        f"  Message : {message!r}\n"
        f"  Score   : {result.score}\n"
        f"  Reason  : {result.reason}"
    )


def test_off_topic_response_text_is_exact() -> None:
    """The decline message must match the requirement exactly."""
    assert OFF_TOPIC_RESPONSE == (
        "I'm MediGuide AI, an assistant focused on health and medical information. "
        "I can help with symptoms, general health concerns, medications and wellness. "
        "Feel free to ask a health-related question."
    )


# ===========================================================================
# 3. AMBIGUOUS inputs — must be passed through (fail-open, is_medical=True)
# ===========================================================================


AMBIGUOUS_INPUTS = [
    # These could be medical or not, but the filter must not block them.
    "Is it normal to feel tired all the time?",         # "tired" is a medical keyword
    "Can stress cause physical symptoms?",              # borderline but medical
    "What does it mean to have a healthy lifestyle?",   # "healthy" is positive
    "How important is sleep for overall wellbeing?",    # wellness keywords present
    "Are there natural ways to boost energy levels?",   # general wellness
    "I'm not feeling well today.",                      # short, vague
]


@pytest.mark.parametrize("message", AMBIGUOUS_INPUTS)
def test_ambiguous_inputs_are_passed_through(message: str) -> None:
    result = check_relevance(message)
    assert result.is_medical is True, (
        f"Ambiguous input was incorrectly rejected.\n"
        f"  Message : {message!r}\n"
        f"  Score   : {result.score}\n"
        f"  Reason  : {result.reason}"
    )


# ===========================================================================
# 4. EMERGENCY inputs — must never be blocked by the relevance filter
#    (they are handled upstream, but the relevance filter must also pass them)
# ===========================================================================


EMERGENCY_INPUTS = [
    "I can't breathe and my chest hurts badly.",
    "My father passed out and won't wake up.",
    "There is uncontrolled bleeding from a cut on my arm.",
    "I think I'm having a stroke — sudden face droop and slurred speech.",
    "I want to kill myself, I feel hopeless.",
]


@pytest.mark.parametrize("message", EMERGENCY_INPUTS)
def test_emergency_inputs_pass_relevance_filter(message: str) -> None:
    """Emergencies have rich medical vocabulary — they must score positively."""
    result = check_relevance(message)
    assert result.is_medical is True, (
        f"Emergency message was incorrectly rejected by the relevance filter.\n"
        f"  Message : {message!r}\n"
        f"  Score   : {result.score}\n"
        f"  Reason  : {result.reason}"
    )


@pytest.mark.parametrize("message", EMERGENCY_INPUTS)
def test_emergency_detected_by_safety_module(message: str) -> None:
    """Confirm the upstream safety module still identifies these as emergencies."""
    assessment = assess_input(message)
    assert assessment.category == "emergency", (
        f"Expected category='emergency' but got {assessment.category!r}\n"
        f"  Message : {message!r}"
    )


# ===========================================================================
# 5. CONTEXTUAL follow-up questions in a medical conversation
# ===========================================================================


MEDICAL_FOLLOWUP_INPUTS = [
    "How long does that take to heal?",
    "Should I see a doctor about this?",
    "Will it get worse if I ignore it?",
    "What else can I do to help?",
    "Can you tell me more?",
    "Is that serious?",
    "Yes, I understand. What should I avoid eating?",
    "How much of it should I take?",
    "Thank you. Can you explain the side effects?",
]


@pytest.mark.parametrize("message", MEDICAL_FOLLOWUP_INPUTS)
def test_medical_followup_in_medical_context(message: str) -> None:
    """Short follow-ups after a medical assistant turn must be accepted."""
    result = check_relevance(message, conversation_history=_medical_history())
    assert result.is_medical is True, (
        f"Medical follow-up was incorrectly rejected.\n"
        f"  Message : {message!r}\n"
        f"  Reason  : {result.reason}"
    )
    assert result.reason == "followup_pass", (
        f"Expected reason='followup_pass', got {result.reason!r}."
    )


@pytest.mark.parametrize("message", MEDICAL_FOLLOWUP_INPUTS)
def test_followup_NOT_passed_after_nonmedical_context(message: str) -> None:
    """The same short follow-ups after a clearly non-medical conversation must
    NOT receive the followup_pass bypass — they should be scored normally.
    They may still be passed as ambiguous, but not via followup shortcut."""
    result = check_relevance(message, conversation_history=_nonmedical_history())
    assert result.reason != "followup_pass", (
        f"Follow-up bypass should not fire after a non-medical assistant turn.\n"
        f"  Message : {message!r}\n"
        f"  Reason  : {result.reason}"
    )


def test_followup_without_history_is_scored_normally() -> None:
    """Without any prior history, follow-up patterns must be scored, not bypassed."""
    result = check_relevance("Should I take it with food?", conversation_history=None)
    # It should still be accepted because the message is short (<= 12 chars? No, it is 28).
    # The important assertion is that reason is NOT followup_pass.
    assert result.reason != "followup_pass"


# ===========================================================================
# 6. Greeting / opener edge cases
# ===========================================================================


GREETINGS = [
    "Hi",
    "Hello",
    "Hey there!",
    "Good morning",
    "Good evening.",
    "Who are you?",
    "What can you do?",
    "I need help",
    "Can you help me?",
]


@pytest.mark.parametrize("message", GREETINGS)
def test_greetings_are_always_accepted(message: str) -> None:
    result = check_relevance(message)
    assert result.is_medical is True
    assert result.reason in {"greeting_pass", "short_pass"}


# ===========================================================================
# 7. Classifier resilience — exceptions must never silently reject medical msgs
# ===========================================================================


def test_empty_message_passes() -> None:
    result = check_relevance("")
    assert result.is_medical is True
    assert result.reason == "empty_pass"


def test_very_long_unrelated_message_is_still_rejected() -> None:
    """Even a very long message with only off-topic signals should be rejected."""
    msg = (
        "I want to write a Python program that uses a database and an algorithm "
        "to solve a quadratic equation and then compile it with a JavaScript framework "
        "and deploy it with Docker on the Azure cloud platform. "
        "Can you help me with the code and the SQL syntax?"
    )
    result = check_relevance(msg)
    assert result.is_medical is False, (
        f"Expected rejection but got is_medical=True (score={result.score})"
    )


def test_mixed_medical_and_unrelated_leans_medical() -> None:
    """A message with both medical and off-topic words should be accepted
    when medical signals dominate (fail-open)."""
    msg = (
        "I have been having chest pain and shortness of breath, and by the way "
        "I also enjoy watching movies on Netflix."
    )
    result = check_relevance(msg)
    # Medical signals (chest pain, shortness of breath) are strong (+3+3) and
    # entertainment signals (movie, Netflix) are only -2 each → should pass.
    assert result.is_medical is True


def test_score_function_positive_for_medical_text() -> None:
    assert _score("I have severe chest pain and difficulty breathing") > 0


def test_score_function_negative_for_coding_text() -> None:
    assert _score("Write a Python algorithm using a database") < 0


def test_score_zero_for_neutral_text() -> None:
    # Purely neutral text with no keywords in either direction.
    assert _score("I went for a walk today.") == 0


# ===========================================================================
# 8. RelevanceResult dataclass contract
# ===========================================================================


def test_relevance_result_is_immutable() -> None:
    result = RelevanceResult(is_medical=True, score=5, reason="medical_pass")
    with pytest.raises((AttributeError, TypeError)):
        result.is_medical = False  # type: ignore[misc]


def test_relevance_result_fields() -> None:
    result = check_relevance("I have a headache and fever.")
    assert isinstance(result.is_medical, bool)
    assert isinstance(result.score, int)
    assert isinstance(result.reason, str)
    assert result.reason in {
        "empty_pass", "short_pass", "greeting_pass",
        "followup_pass", "medical_pass", "ambiguous_pass", "off_topic_reject",
    }
