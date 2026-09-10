import time
import uuid

from mediguide.config import settings
from mediguide.llm import LLMService
from mediguide.safety import assess_input, emergency_response
from analytics import log_interaction


def classify_topic(question: str) -> str:
    question_lower = question.casefold()

    topic_keywords = {
        "Nutrition": [
            "food",
            "diet",
            "nutrition",
            "vitamin",
            "protein",
            "iron",
            "calorie",
            "meal"
        ],
        "Symptoms": [
            "pain",
            "headache",
            "fever",
            "cough",
            "dizzy",
            "symptom",
            "nausea",
            "vomit"
        ],
        "Medication": [
            "medicine",
            "medication",
            "tablet",
            "drug",
            "dose",
            "ibuprofen",
            "paracetamol",
            "antibiotic"
        ],
        "Sleep & Wellness": [
            "sleep",
            "stress",
            "exercise",
            "workout",
            "relax",
            "tired",
            "wellness"
        ],
        "Mental Wellness": [
            "anxiety",
            "depression",
            "mental",
            "panic",
            "sad"
        ]
    }

    for topic, keywords in topic_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            return topic

    return "General"


def run_cli() -> None:
    if not settings.api_key:
        raise ValueError(
            "OPENROUTER_API_KEY was not found. Check your .env file."
        )

    service = LLMService(settings)
    history: list[dict] = []

    session_id = str(uuid.uuid4())[:8]

    print(
        "MediGuide AI - general health information "
        "(type 'exit' to close)"
    )

    while True:
        question = input("You: ").strip()

        if question.casefold() in {"exit", "quit"}:
            print("Take care.")
            return

        if not question:
            print("Please enter a question.")
            continue

        # Check for emergency situations before sending the question to the LLM
        if assess_input(question).category == "emergency":
            print(emergency_response())
            continue

        # Add user question to conversation history
        history.append({
            "role": "user",
            "content": question
        })

        started = time.perf_counter()

        try:
            response = "".join(
                text for text, _ in service.stream(history)
            )

        except Exception:
            # Remove the failed user message from history
            history.pop()

            response_time = time.perf_counter() - started

            try:
                log_interaction(
                    session_id,
                    response_time,
                    len(history) // 2,
                    classify_topic(question),
                    "error"
                )
            except Exception:
                pass

            print(
                "Sorry, MediGuide could not process "
                "that request right now."
            )
            continue

        # Add AI response to conversation history
        history.append({
            "role": "assistant",
            "content": response
        })

        response_time = time.perf_counter() - started

        print(
            f"MediGuide ({response_time:.2f}s): "
            f"{response}\n"
        )

        # Classify the question for analytics
        topic = classify_topic(question)

        # Store interaction analytics
        try:
            log_interaction(
                session_id,
                response_time,
                len(history) // 2,
                topic,
                "success"
            )
        except Exception:
            # Analytics failure should never stop the chatbot
            pass


if __name__ == "__main__":
    run_cli()