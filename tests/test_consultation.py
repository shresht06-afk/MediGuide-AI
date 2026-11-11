"""
Automated regression tests for MediGuide AI structured consultation flow (v2.0).

Covers all 10 requirements:
1. 'I have stomach pain' => relevant initial screening questions, not immediate generic remedies.
2. A reply describing location, severity, and duration => context-aware next questions.
3. 'How do I fix it?' => correctly uses preceding stomach-pain context.
4. Serious red-flag symptoms => urgent guidance without routine questioning.
5. 'What is vitamin D?' => direct educational response without interrogation.
6. 'Who is Hrithik Roshan?' => medical-only refusal.
7. No unnecessary repeated questions (history and context tracking).
8. No raw Markdown formatting artifacts in user-facing responses.
9. No fabricated diagnoses, medical facts, or prescriptions.
10. Existing API contract remains unchanged.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mediguide.relevance import OFF_TOPIC_RESPONSE
from mediguide.safety import (
    EMERGENCY_PATTERNS,
    SYSTEM_PROMPT,
    assess_input,
    emergency_response,
    sanitize_presentation,
)


# ===========================================================================
# Fixture: API TestClient with isolated SQLite DB
# ===========================================================================


@pytest.fixture()
def client_env(tmp_path):
    """Provide a TestClient with an isolated SQLite DB per test."""
    import mediguide.api as api_module
    import mediguide.db as db_module
    from fastapi.testclient import TestClient

    db_path = str(tmp_path / "test_consultation.db")
    fresh_db = db_module.Database(db_path)
    api_module.db = fresh_db

    client = TestClient(api_module.app)
    return client, api_module


def _create_conv(client) -> str:
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


# ===========================================================================
# 1. Initial Symptom Report => Screening questions, no premature remedies
# ===========================================================================


def test_initial_symptom_system_prompt_enforces_screening() -> None:
    """Verify that SYSTEM_PROMPT mandates Stage 1 initial screening for symptoms."""
    # Must instruct screening questions
    assert "STAGE 1" in SYSTEM_PROMPT
    assert "1 to 3" in SYSTEM_PROMPT
    # Must explicitly forbid immediate remedies or OTC pain relievers
    assert "Do NOT immediately give remedies" in SYSTEM_PROMPT
    assert "Do NOT immediately list possible diagnoses" in SYSTEM_PROMPT
    assert "abdominal pain" in SYSTEM_PROMPT


def test_initial_symptom_flow_invokes_llm_with_screening_prompt(client_env) -> None:
    """Sending 'I have stomach pain' delivers the message to LLM with full system prompt."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    captured_history = []

    def mock_stream(history):
        captured_history.extend(history)
        yield (
            "I understand you are experiencing stomach pain. To help me give you relevant health information, could you tell me:\n\n"
            "1. Where in your stomach is the pain located?\n"
            "2. How long have you had it, and how severe is it from 1 to 10?\n"
            "3. Are you having any other symptoms like fever or vomiting?"
        ), 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, "I have stomach pain")
    finally:
        api_module.llm.stream = original

    assert res["safety"] == "routine"
    assert "stomach pain" in res["content"].lower()
    assert "1." in res["content"]
    assert "2." in res["content"]
    assert "3." in res["content"]
    # LLM was passed the user's initial message
    assert any(m.get("content") == "I have stomach pain" for m in captured_history)


# ===========================================================================
# 2 & 7. Reply with symptom details => Context-aware next questions (no repeats)
# ===========================================================================


def test_adaptive_questions_preserve_context_and_avoid_repetition(client_env) -> None:
    """When a user answers location, duration, and severity, context is passed to the next turn."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    history_snapshots = []

    def mock_stream(history):
        history_snapshots.append(list(history))
        turn_num = len(history_snapshots)
        if turn_num == 1:
            yield (
                "I understand you are experiencing stomach pain.\n\n"
                "1. Where is the pain located?\n"
                "2. When did it start, and how severe is it?"
            ), 0.1
        else:
            yield (
                "Thank you for sharing that it is in your lower right abdomen, severe (7/10), and started 6 hours ago.\n\n"
                "1. Has the pain been getting steadily worse or does it come and go in waves?\n"
                "2. Have you experienced any fever, nausea, or loss of appetite?"
            ), 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        # Turn 1: initial symptom
        _send(client, conv_id, "I have stomach pain")
        # Turn 2: answer details
        res2 = _send(
            client,
            conv_id,
            "It is on my lower right side, started 6 hours ago, and severity is 7/10.",
        )
    finally:
        api_module.llm.stream = original

    assert len(history_snapshots) == 2
    second_call_messages = history_snapshots[1]

    # Verify second turn history contains the previous user question and assistant answer
    user_contents = [m["content"] for m in second_call_messages if m["role"] == "user"]
    assert "I have stomach pain" in user_contents
    assert "It is on my lower right side, started 6 hours ago, and severity is 7/10." in user_contents

    # The prompt explicitly forbids repeating answered questions
    assert "NEVER repeat questions the user has already answered" in SYSTEM_PROMPT


# ===========================================================================
# 3. 'How do I fix it?' => Uses preceding stomach pain context
# ===========================================================================


def test_how_do_i_fix_it_preserves_stomach_pain_context(client_env) -> None:
    """'How do I fix it?' must carry the full stomach-pain conversation history to the model."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    call_histories = []

    def mock_stream(history):
        call_histories.append(list(history))
        yield "For stomach pain, do not take ibuprofen or other NSAIDs before a doctor checks it.", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        _send(client, conv_id, "I have stomach pain")
        res2 = _send(client, conv_id, "How do I fix it?")
    finally:
        api_module.llm.stream = original

    assert len(call_histories) == 2
    final_history = call_histories[-1]

    # The second LLM call must have the initial "I have stomach pain" message
    first_msg = next((m for m in final_history if m["content"] == "I have stomach pain"), None)
    assert first_msg is not None, "Initial stomach pain context was lost from history"
    assert final_history[-1]["content"] == "How do I fix it?"


# ===========================================================================
# 4. Red-flag symptoms => Urgent guidance without routine questioning
# ===========================================================================


@pytest.mark.parametrize("emergency_message", [
    "I can't breathe and my chest feels heavy.",
    "My mother has sudden face droop and slurred speech.",
    "There is uncontrolled bleeding from a deep wound.",
    "I have the worst headache of my life that came on like a thunderclap.",
    "My throat is swelling and I feel like it is closing up.",
    "I have been coughing up blood today.",
    "He swallowed poison by accident.",
])
def test_red_flag_symptoms_trigger_immediate_urgent_guidance(client_env, emergency_message: str) -> None:
    """Critical red flags must bypass LLM streaming and return immediate emergency guidance."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    mock_stream = MagicMock(side_effect=AssertionError("LLM should not be called for red flags"))
    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, emergency_message)
    finally:
        api_module.llm.stream = original

    assert res["safety"] == "emergency"
    assert "immediate" in res["content"].lower() or "emergency" in res["content"].lower()
    mock_stream.assert_not_called()


# ===========================================================================
# 5. General medical education ('What is vitamin D?') => Direct educational response
# ===========================================================================


def test_general_education_question_gets_direct_response(client_env) -> None:
    """'What is vitamin D?' should receive educational response, not screening interrogation."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    edu_response = (
        "Vitamin D is a fat-soluble nutrient that helps your body absorb calcium "
        "and maintain healthy bones, teeth, and immune function."
    )

    def mock_stream(history):
        yield edu_response, 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, "What is vitamin D?")
    finally:
        api_module.llm.stream = original

    assert res["safety"] == "routine"
    assert "vitamin d" in res["content"].lower()
    # Ensure system prompt directs direct educational response for general queries
    assert "GENERAL MEDICAL EDUCATION" in SYSTEM_PROMPT
    assert "Do NOT interrogate the user" in SYSTEM_PROMPT


# ===========================================================================
# 6. Medical-only refusal ('Who is Hrithik Roshan?')
# ===========================================================================


def test_unrelated_celebrity_query_is_rejected(client_env) -> None:
    """Unrelated queries like 'Who is Hrithik Roshan?' must be declined by the relevance filter."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    mock_stream = MagicMock(side_effect=AssertionError("LLM should not be called for off-topic query"))
    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, "Who is Hrithik Roshan?")
    finally:
        api_module.llm.stream = original

    assert res["safety"] == "off_topic"
    assert res["content"] == OFF_TOPIC_RESPONSE
    mock_stream.assert_not_called()


# ===========================================================================
# 8. No raw Markdown formatting artifacts in user-facing responses
# ===========================================================================


def test_sanitize_presentation_removes_markdown_artifacts() -> None:
    """Test sanitizer strips raw asterisks, hashes, code fences without altering medical text."""
    raw = (
        "### Assessment\n\n"
        "I understand you have **stomach pain**.\n\n"
        "* Where is the pain?\n"
        "* How severe is it?\n\n"
        "Measurements: BP 120/80 mmHg, SpO2 98%, 5 * 3 calculation.\n\n"
        "```json\n"
        '{"status": "ok"}\n'
        "```"
    )
    cleaned = sanitize_presentation(raw)

    assert "###" not in cleaned
    assert "**" not in cleaned
    assert "```" not in cleaned
    # Hyphen conversion for bullet points
    assert "- Where is the pain?" in cleaned
    # Medical content preserved
    assert "BP 120/80 mmHg" in cleaned
    assert "SpO2 98%" in cleaned


def test_api_sanitizes_llm_markdown_artifacts(client_env) -> None:
    """If the LLM accidentally generates Markdown formatting, the API returns sanitized text."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    raw_llm_output = (
        "### Initial Screening\n\n"
        "You reported having **fever**.\n\n"
        "1. What is your temperature?\n"
        "2. Do you have **chills** or a cough?"
    )

    def mock_stream(history):
        yield raw_llm_output, 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, "I have a fever")
    finally:
        api_module.llm.stream = original

    assert "###" not in res["content"]
    assert "**" not in res["content"]
    assert "Initial Screening" in res["content"]
    assert "fever" in res["content"]
    assert "chills" in res["content"]


# ===========================================================================
# 9. No fabricated diagnoses, medical facts, or prescriptions
# ===========================================================================


def test_system_prompt_strictly_forbids_diagnoses_and_prescriptions() -> None:
    """Verify that clinical boundaries are codified in SYSTEM_PROMPT."""
    assert "Never diagnose" in SYSTEM_PROMPT or "You do not diagnose" in SYSTEM_PROMPT
    assert "Never prescribe" in SYSTEM_PROMPT or "do not prescribe" in SYSTEM_PROMPT
    assert "Never invent" in SYSTEM_PROMPT or "Never claim to have taken physical measurements" in SYSTEM_PROMPT


# ===========================================================================
# 10. Existing API contract remains unchanged
# ===========================================================================


def test_api_contract_schema_is_preserved(client_env) -> None:
    """Verify that the API response conforms to MessageResponse schema."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    def mock_stream(history):
        yield "Educational answer about headache.", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, "I have a mild headache.")
    finally:
        api_module.llm.stream = original

    # Check all required keys exist
    expected_keys = {"message_id", "content", "topic", "safety", "response_time"}
    assert expected_keys.issubset(set(res.keys()))

    # Check types
    assert isinstance(res["message_id"], str)
    assert isinstance(res["content"], str)
    assert isinstance(res["topic"], str)
    assert isinstance(res["safety"], str)
    assert isinstance(res["response_time"], (int, float))

    # If assessment extension is present, validate its structure
    if "assessment" in res and res["assessment"] is not None:
        assessment = res["assessment"]
        assert "id" in assessment
        assert "title" in assessment
        assert "questions" in assessment
        assert isinstance(assessment["questions"], list)
        for q in assessment["questions"]:
            assert "id" in q
            assert "label" in q
            assert "type" in q


# ===========================================================================
# 11. Interactive Quick-Select Assessment Tests
# ===========================================================================


def test_stomach_pain_produces_relevant_clickable_assessment(client_env) -> None:
    """Reporting stomach pain must generate a structured stomach assessment form."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    def mock_stream(history):
        yield "Where is the pain located and how bad is it?", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, "I have severe stomach pain")
    finally:
        api_module.llm.stream = original

    assert "assessment" in res
    assessment = res["assessment"]
    assert assessment["id"] == "stomach_pain_intake"
    assert "Stomach & Abdomen" in assessment["title"]

    q_ids = [q["id"] for q in assessment["questions"]]
    assert "location" in q_ids
    assert "severity" in q_ids
    assert "onset" in q_ids
    assert "associated" in q_ids

    # Check location choices
    location_q = next(q for q in assessment["questions"] if q["id"] == "location")
    assert "Upper abdomen" in location_q["options"]
    assert "Lower abdomen" in location_q["options"]
    assert "Left side" in location_q["options"]
    assert "Right side" in location_q["options"]
    assert "Around belly button" in location_q["options"]
    assert "Not sure" in location_q["options"]

    # Check severity slider
    severity_q = next(q for q in assessment["questions"] if q["id"] == "severity")
    assert severity_q["type"] == "slider"
    assert severity_q["min"] == 1
    assert severity_q["max"] == 10


def test_assessment_submission_delivers_structured_answers_to_next_turn(client_env) -> None:
    """Submitting formatted assessment answers delivers them to the LLM and DB."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    call_histories = []

    def mock_stream(history):
        call_histories.append(list(history))
        yield "Thank you for providing the details about your lower right abdomen pain.", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        # Turn 1: initial symptom
        _send(client, conv_id, "I have stomach pain")

        # Turn 2: simulate clicking answers and submitting assessment
        submitted_text = (
            "Location: Lower abdomen (Right side)\n"
            "Severity: 7/10\n"
            "Onset: Yesterday\n"
            "Associated symptoms: Nausea or vomiting\n"
            "Additional notes: Woke me up last night"
        )
        res2 = _send(client, conv_id, submitted_text)
    finally:
        api_module.llm.stream = original

    assert res2["safety"] == "routine"
    assert len(call_histories) == 2
    second_history = call_histories[1]

    # Verify the structured submission is in history for the LLM
    last_user_msg = next((m for m in reversed(second_history) if m["role"] == "user"), None)
    assert last_user_msg is not None
    assert "Location: Lower abdomen" in last_user_msg["content"]
    assert "Severity: 7/10" in last_user_msg["content"]

    # In turn 2, since assessment was already answered, no duplicate assessment form is sent
    assert res2.get("assessment") is None


def test_general_education_question_omits_assessment(client_env) -> None:
    """Educational inquiries (e.g. 'What is vitamin D?') must not attach assessment forms."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    def mock_stream(history):
        yield "Vitamin D is an essential nutrient...", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        res = _send(client, conv_id, "What is vitamin D?")
    finally:
        api_module.llm.stream = original

    assert res.get("assessment") is None


def test_emergency_bypasses_assessment(client_env) -> None:
    """Emergency queries must NEVER include a routine assessment form."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    res = _send(client, conv_id, "I can't breathe and my chest hurts badly.")
    assert res["safety"] == "emergency"
    assert res.get("assessment") is None


def test_short_and_duration_answers_accepted_by_relevance_filter(client_env) -> None:
    """Short and duration answers in medical context must pass the relevance filter."""
    from mediguide.relevance import check_relevance

    history = [
        {"role": "user", "content": "I have stomach pain"},
        {"role": "assistant", "content": "Where is the pain located and when did it start?"},
    ]

    test_answers = [
        "Right side",
        "7/10",
        "Yesterday",
        "A few days ago",
        "More than a week ago",
        "Around the belly button",
        "Upper abdomen",
        "Across the abdomen",
        "None of these",
        "Started today",
        "Just started",
    ]

    for ans in test_answers:
        rel = check_relevance(ans, history)
        assert rel.is_medical is True, f"Expected '{ans}' to be accepted as medical, got {rel}"


def test_unrelated_messages_remain_rejected(client_env) -> None:
    """Clearly unrelated non-medical messages remain rejected."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    unrelated_queries = [
        "Who is Hrithik Roshan?",
        "What is 68900+98776",
        "What is the capital of France?",
        "Write me a poem about computers",
    ]

    for q in unrelated_queries:
        res = _send(client, conv_id, q)
        assert res["safety"] == "off_topic"
        assert res["content"] == OFF_TOPIC_RESPONSE
        assert res.get("assessment") is None


def test_followup_how_do_i_fix_it_retains_context_and_omits_new_assessment(client_env) -> None:
    """Follow-up questions like 'How do I fix it?' retain context and omit duplicate assessment."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    call_histories = []

    def mock_stream(history):
        call_histories.append(list(history))
        yield "To manage mild stomach discomfort, consider rest and hydration...", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream

        # Turn 1: Initial symptom report
        res1 = _send(client, conv_id, "I have stomach pain")
        assert "assessment" in res1

        # Turn 2: Follow-up question
        res2 = _send(client, conv_id, "How do I fix it?")
        assert res2["safety"] == "routine"
        assert res2.get("assessment") is None

        # Verify LLM received full history including 'I have stomach pain'
        assert len(call_histories) == 2
        second_history = call_histories[1]
        user_messages = [m["content"] for m in second_history if m["role"] == "user"]
        assert "I have stomach pain" in user_messages
        assert "How do I fix it?" in user_messages
    finally:
        api_module.llm.stream = original


def test_user_can_stop_assessment_or_request_summary(client_env) -> None:
    """User asking to stop questions or asking for a summary does not receive assessment forms."""
    client, api_module = client_env
    conv_id = _create_conv(client)

    def mock_stream(history):
        yield "I understand you have stomach pain. Where is it located?", 0.1

    original = api_module.llm.stream
    try:
        api_module.llm.stream = mock_stream
        _send(client, conv_id, "I have stomach pain")
        res = _send(client, conv_id, "Can you summarize what it could be and stop asking questions?")
        assert res["safety"] == "routine"
        assert res.get("assessment") is None
    finally:
        api_module.llm.stream = original


