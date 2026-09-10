import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import settings
from .db import Database
from .llm import LLMService
from .safety import assess_input, emergency_response
from .topics import classify

db = Database(settings.database)
llm = LLMService(settings)


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=0, le=1)
    comment: str | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="MediGuide AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "provider_configured": bool(settings.api_key)}


@app.post("/api/conversations")
def create_conversation() -> dict:
    conversation = db.create_conversation()
    db.event("conversation_started", conversation["id"])
    return conversation


@app.get("/api/conversations")
def conversations() -> list[dict]:
    return db.list_conversations()


@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id: str) -> dict:
    item = db.get_conversation(conversation_id)
    if not item:
        raise HTTPException(404, "Conversation not found.")
    return item


@app.post("/api/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, request: MessageRequest) -> dict:
    item = db.get_conversation(conversation_id)
    if not item:
        raise HTTPException(404, "Conversation not found.")
    assessment = assess_input(request.content)
    topic = classify(request.content)
    db.add_message(conversation_id, "user", request.content, topic=topic.name)
    db.event("user_message_sent", conversation_id, topic.name)
    if assessment.category == "emergency":
        response = emergency_response()
        message_id = db.add_message(conversation_id, "assistant", response, topic=topic.name)
        db.event("emergency_warning_triggered", conversation_id, topic.name, status="success")
        return {"message_id": message_id, "content": response, "topic": topic.name, "safety": assessment.category, "response_time": 0}
    history = [{"role": row["role"], "content": row["content"]} for row in item["messages"][-10:]]
    history.append({"role": "user", "content": request.content})
    started = time.perf_counter()
    try:
        content = "".join(text for text, _ in llm.stream(history))
    except Exception as error:
        db.event("response_error", conversation_id, topic.name, response_time=time.perf_counter() - started, status="error", metadata={"type": type(error).__name__})
        raise HTTPException(503, "MediGuide is temporarily unavailable. Please try again.") from error
    elapsed = time.perf_counter() - started
    message_id = db.add_message(conversation_id, "assistant", content, elapsed, topic.name)
    db.event("ai_response_generated", conversation_id, topic.name, elapsed, "success")
    return {"message_id": message_id, "content": content, "topic": topic.name, "safety": "routine", "response_time": round(elapsed, 2)}


@app.post("/api/messages/{message_id}/feedback")
def feedback(message_id: str, request: FeedbackRequest) -> dict:
    db.add_feedback(message_id, request.rating, request.comment)
    db.event("feedback_submitted", metadata={"rating": request.rating})
    return {"status": "recorded"}


@app.get("/api/analytics/summary")
def analytics_summary() -> dict:
    return db.metrics()
