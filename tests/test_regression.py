"""
Regression tests for MediGuide AI medical-only relevance gate  — v2 bugfix.

UNIT tests: no network, no LLM, fully offline.
API tests:  real FastAPI TestClient, LLM stream() fully mocked.

Run with:
    python -m pytest tests/test_regression.py -v
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock

from mediguide.relevance import check_relevance, OFF_TOPIC_RESPONSE, _score
from mediguide.safety import assess_input


# ===========================================================================
# Shared helpers
# ===========================================================================

MEDICAL_HISTORY = [
    {
        "role": "user",
        "content": "I have been having frequent headaches for the past week.",
    },
    {
        "role": "assistant",
        "content": (
            "Frequent headaches can be caused by tension, dehydration, poor sleep "
            "or migraine.  If they persist, please see a doctor to rule out any "
            "serious cause including hypertension."
        ),
    },
]

NONMEDICAL_HISTORY = [
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."},
]


# ===========================================================================
# 1. CONFIRMED BUG REGRESSION
# ===========================================================================

@pytest.mark.parametrize("message", [
    "who is hritik roshan?",
    "who is Hrithik Roshan?",
])
def test_celebrity_query_is_rejected(message: str) -> None:
    """Bug v1: celebrity queries scored 0 -> ambiguous_pass -> LLM answered."""
    result = check_relevance(message)
    assert result.is_medical is False, (
        f"Celebrity query must be rejected.\n"
        f"  Message: {message!r}  Score: {result.score}  Reason: {result.reason}"
    )
    assert result.reason == "off_topic_reject"


@pytest.mark.parametrize("message", [
    "what is 68900+98776",
    "what is 68900 + 98776?",
    "calculate 500 * 24",
    "what is 100 divided by 4",
    "how much is 350 + 650",
])
def test_arithmetic_expression_is_rejected(message: str) -> None:
    """Bug v1: raw digit+operator expressions had no negative pattern -> scored 0 -> passed."""
    result = check_relevance(message)
    assert result.is_medical is False, (
        f"Arithmetic expression must be rejected.\n"
        f"  Message: {message!r}  Score: {result.score}  Reason: {result.reason}"
    )


# ===========================================================================
# 2. MEDICAL questions — must always be accepted
# ===========================================================================

@pytest.mark.parametrize("message", [
    "What causes frequent headaches?",
    "What are the symptoms of diabetes?",
    "How can I improve my sleep?",
    "I have chest pain and trouble breathing.",
    "What is the difference between ibuprofen and paracetamol?",
    "How do I manage anxiety without medication?",
    "What foods should I avoid with high blood pressure?",
    "My child has had a fever for two days. When should I see a doctor?",
    "What is the recommended daily vitamin D intake?",
    "How long does a sprained ankle take to heal?",
    "What are the early warning signs of a stroke?",
    "Is it safe to take aspirin during pregnancy?",
    "How do I perform CPR on an adult?",
    "What causes insomnia and how can I fix it?",
    "What are the side effects of metformin?",
])
def test_medical_question_is_accepted(message: str) -> None:
    result = check_relevance(message)
    assert result.is_medical is True, (
        f"Medical question was incorrectly rejected.\n"
        f"  Message: {message!r}  Score: {result.score}  Reason: {result.reason}"
    )


# ===========================================================================
# 3. EMERGENCY inputs
# ===========================================================================

@pytest.mark.parametrize("message", [
    "I have chest pain and trouble breathing.",
    "My father passed out and won't wake up.",
    "There is uncontrolled bleeding that won't stop.",
    "I think I'm having a stroke — face droop and slurred speech.",
    "I want to kill myself.",
])
def test_emergency_passes_relevance_filter(message: str) -> None:
    result = check_relevance(message)
    assert result.is_medical is True, (
        f"Emergency must not be blocked by relevance filter.\n"
        f"  Message: {message!r}  Score: {result.score}  Reason: {result.reason}"
    )


@pytest.mark.parametrize("message", [
    "I have chest pain and trouble breathing.",
    "My father passed out and won't wake up.",
    "There is uncontrolled bleeding that won't stop.",
    "I think I'm having a stroke — face droop and slurred speech.",
    "I want to kill myself.",
])
def test_emergency_detected_by_safety_module(message: str) -> None:
    assessment = assess_input(message)
    assert assessment.category == "emergency", (
        f"Expected 'emergency', got {assessment.category!r}  |  Message: {message!r}"
    )


# ===========================================================================
# 4. Context-sensitive follow-ups after a medical conversation
# ===========================================================================

@pytest.mark.parametrize("message", [
    "What if it happens every morning?",
    "How long does that take to heal?",
    "Should I see a doctor about this?",
    "Will it get worse if I ignore it?",
    "What else can I do to help?",
    "Is that serious?",
    "How much should I take?",
])
def test_medical_followup_accepted_after_medical_context(message: str) -> None:
    result = check_relevance(message, conversation_history=MEDICAL_HISTORY)
    assert result.is_medical is True, (
        f"Medical follow-up was incorrectly rejected.\n"
        f"  Message: {message!r}  Reason: {result.reason}"
    )
    assert result.reason == "followup_pass"


# ===========================================================================
# 5. Geography must be rejected EVEN after a medical conversation
# ===========================================================================

def test_geography_rejected_after_medical_context() -> None:
    result = check_relevance(
        "What is the capital of France?",
        conversation_history=MEDICAL_HISTORY,
    )
    assert result.is_medical is False, (
        f"Geography must be rejected even in medical context.\n"
        f"  Score: {result.score}  Reason: {result.reason}"
    )


def test_celebrity_rejected_after_medical_context() -> None:
    result = check_relevance(
        "who is Hrithik Roshan?",
        conversation_history=MEDICAL_HISTORY,
    )
    assert result.is_medical is False


# ===========================================================================
# 6. Other unrelated requests — all must be rejected
# ===========================================================================

@pytest.mark.parametrize("message", [
    "Write Python code for sorting a list.",
    "Explain the React framework.",
    "What is a Docker container?",
    "Can you debug this JavaScript function?",
    "What is the capital of France?",
    "Who won the FIFA World Cup last year?",
    "Recommend a good Netflix series.",
    "What is the current Bitcoin price?",
    "Translate this text into Spanish.",
    "Write me an essay about climate change.",
])
def test_unrelated_requests_are_rejected(message: str) -> None:
    result = check_relevance(message)
    assert result.is_medical is False, (
        f"Off-topic request must be rejected.\n"
        f"  Message: {message!r}  Score: {result.score}  Reason: {result.reason}"
    )


def test_off_topic_response_text_is_exact() -> None:
    assert OFF_TOPIC_RESPONSE == (
        "I'm MediGuide AI, an assistant focused on health and medical information. "
        "I can help with symptoms, general health concerns, medications and wellness. "
        "Feel free to ask a health-related question."
    )


# ===========================================================================
# 7. API ROUTE TESTS — FastAPI TestClient, LLM fully mocked
# ===========================================================================

@pytest.fixture()
def api_client(tmp_path):
    """
    Build a TestClient using the real FastAPI app but with:
    - An isolated file-based SQLite database (temp dir, fresh per test).
      NOTE: SQLite :memory: is single-connection scoped; it cannot be shared across
      multiple db.connect() calls in mediguide.db.Database.
    - The LLM client replaced by a controllable mock.
    """
    import mediguide.db as db_module
    import mediguide.api as api_module

    db_path = str(tmp_path / "test_medi.db")
    fresh_db = db_module.Database(db_path)
    api_module.db = fresh_db

    from fastapi.testclient import TestClient
    client = TestClient(api_module.app)
    return client, api_module


def _create_conv(client):
    resp = client.post("/api/conversations")
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _send(client, conv_id: str, content: str) -> dict:
    resp = client.post(
        f"/api/conversations/{conv_id}/messages",
        json={"content": content},
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()


# --- 7a. Off-topic — LLM must NEVER be called ---------------------------------

@pytest.mark.parametrize("message", [
    "who is hritik roshan?",
    "who is Hrithik Roshan?",
    "what is 68900+98776",
    "Write Python code for a bubble sort.",
    "What is the capital of Australia?",
    "Recommend a Netflix series for me.",
])
def test_api_rejects_unrelated_and_never_calls_llm(api_client, message: str) -> None:
    client, api_module = api_client
    conv_id = _create_conv(client)

    mock_stream = MagicMock(side_effect=AssertionError(
        f"LLM stream() was called for off-topic message: {message!r}"
    ))
    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        body = _send(client, conv_id, message)
    finally:
        api_module.llm.stream = original

    assert body["content"] == OFF_TOPIC_RESPONSE, (
        f"Expected off-topic response body.\n  Got: {body['content']!r}"
    )
    assert body["safety"] == "off_topic"
    mock_stream.assert_not_called()


# --- 7b. Medical — LLM IS called and its response is returned -----------------

@pytest.mark.parametrize("message", [
    "What causes frequent headaches?",
    "What are the symptoms of diabetes?",
    "How can I improve my sleep?",
])
def test_api_passes_medical_to_llm(api_client, message: str) -> None:
    client, api_module = api_client
    conv_id = _create_conv(client)

    fake_answer = "Mocked medical answer from LLM."

    def fake_stream(history):
        yield fake_answer, 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = fake_stream
        body = _send(client, conv_id, message)
    finally:
        api_module.llm.stream = original

    assert body["content"] == fake_answer
    assert body["safety"] == "routine"
    assert body["response_time"] >= 0


# --- 7c. Emergency — emergency_response returned, LLM NOT called --------------

def test_api_emergency_bypasses_llm(api_client) -> None:
    client, api_module = api_client
    conv_id = _create_conv(client)

    mock_stream = MagicMock(side_effect=AssertionError(
        "LLM stream() was called for an emergency message"
    ))
    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        body = _send(client, conv_id, "I have chest pain and trouble breathing.")
    finally:
        api_module.llm.stream = original

    assert body["safety"] == "emergency"
    assert "immediate" in body["content"].lower() or "emergency" in body["content"].lower()
    mock_stream.assert_not_called()


# --- 7d. Follow-up in medical context — LLM IS called twice ------------------

def test_api_medical_followup_passes_to_llm(api_client) -> None:
    client, api_module = api_client
    conv_id = _create_conv(client)
    call_count = [0]

    def counting_stream(history):
        call_count[0] += 1
        yield "Mocked medical answer.", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = counting_stream
        _send(client, conv_id, "What causes frequent headaches?")
        body = _send(client, conv_id, "What if it happens every morning?")
    finally:
        api_module.llm.stream = original

    assert body["safety"] == "routine"
    assert call_count[0] >= 2, (
        f"LLM should have been called at least twice, got {call_count[0]}"
    )


# --- 7e. Geography AFTER medical context — must still be rejected -------------

def test_api_geography_rejected_after_medical_exchange(api_client) -> None:
    client, api_module = api_client
    conv_id = _create_conv(client)

    def fake_stream(history):
        yield "Mocked medical answer about headaches.", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = fake_stream
        _send(client, conv_id, "I have been having frequent headaches.")
        mock_llm = MagicMock(side_effect=AssertionError(
            "LLM called for geography after medical context"
        ))
        api_module.llm.stream = mock_llm
        body = _send(client, conv_id, "What is the capital of France?")
    finally:
        api_module.llm.stream = original

    assert body["content"] == OFF_TOPIC_RESPONSE
    assert body["safety"] == "off_topic"
    mock_llm.assert_not_called()
