# MediGuide AI - Implementation Plan

## Goal

Transform the CLI proof of concept into a portfolio-quality, safety-conscious health-information web application without exposing provider credentials or presenting the system as a medical professional.

## Delivery phases

### Phase 0 - Audit

- Completed repository audit.
- Capture current behavior, defects, risks, and target architecture.

### Phase 1 - Backend foundation

- Add a reproducible dependency manifest and environment configuration.
- Extract the LLM client into a service with explicit error handling and configurable model/timeouts.
- Add deterministic input limits and safety classification for urgent language.
- Preserve a CLI entry point that uses the shared service.

### Phase 2 - FastAPI API

- Create an application factory and health endpoint.
- Add conversation creation, message submission, history, and feedback endpoints.
- Define typed request/response models and stable error responses.
- Support streaming through a server-sent-events endpoint where practical.

### Phase 3 - Persistence

- Add SQLite repositories for conversations, messages, feedback, and analytics events.
- Keep database access behind small modules so the storage engine can change later.
- Avoid persisting raw health text in analytics events.

### Phase 4 - Safety and response quality

- Add emergency-signals detection before model calls.
- Require the model to return structured sections: general information, possible explanations, what the user can do, and when to seek help.
- Validate and normalize model output; clearly label uncertainty and emergency guidance.

### Phase 5 - Analytics

- Record request lifecycle, latency, first-token latency when streaming, outcome, topic, and feedback events.
- Add aggregate KPI endpoints for volume, latency, success rate, topics, and feedback.
- Build a small dashboard view suitable for product/business analysis.

### Phase 6 - Frontend

- Add a React/TypeScript client with a calm navy/teal healthcare design system.
- Implement landing, chat, history, contextual insight, settings, and analytics views.
- Include responsive behavior, keyboard support, loading/error states, and accessible labels.

### Phase 7 - Verification and documentation

- Add targeted unit and API tests.
- Run syntax checks, tests, and a local smoke test.
- Document setup, environment variables, safety scope, architecture, and known limitations.

## Implementation order and acceptance checks

1. Backend modules compile/import without requiring an API key at import time.
2. Health endpoint responds without external services.
3. Validation rejects empty or oversized messages.
4. Conversations and messages survive process restarts through SQLite.
5. Provider failures return safe, stable API errors and do not leak credentials.
6. Emergency language produces immediate professional-help guidance.
7. Analytics aggregates are derived from structured events.
8. Frontend builds and presents the core chat flow on desktop and mobile.
9. Existing CLI behavior remains available through the shared backend services.

## Scope boundaries

Voice, multilingual support, RAG, trusted-source retrieval, appointments, wearable integrations, recommendations, authentication, and experimentation are intentionally deferred. The architecture should leave clear extension points without pretending these capabilities are implemented.
