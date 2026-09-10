# MediGuide AI - Project Audit

## Audit scope

Audited the repository on 2026-08-27 before implementation. The repository currently contains a small Python command-line prototype and a Python virtual environment.

## Current architecture

The application is a single-process CLI:

1. `app.py` loads environment variables and constructs an OpenAI-compatible client pointed at OpenRouter.
2. A module-level `conversation_history` list stores recent messages in memory.
3. User input is sent to `openrouter/free` with a safety-focused system prompt.
4. The response is streamed to the terminal.
5. `analytics.log_interaction` is intended to persist interaction metrics.

There is no web server, browser client, persistent database, authentication boundary, API schema, or service layer.

## Existing files and functionality

| File | Observed purpose |
| --- | --- |
| `app.py` | CLI loop, OpenRouter configuration, safety prompt, in-memory history, streaming, timing, error display |
| `analytics.py` | Imported by `app.py`; the file currently has no implementation content |
| `.env` | Local OpenRouter configuration; must remain untracked |
| `.gitignore` | Existing ignore rules |
| `.vscode/settings.json` | Editor settings |
| `.venv/` | Local Python 3.13 virtual environment; not application source |

Implemented prototype capabilities include environment-based credentials, OpenAI SDK integration, streaming, recent-message truncation, response-time measurement, and a safety-oriented prompt. Analytics logging is currently a broken integration because the imported function is absent.

## Dependencies

No dependency manifest exists at the repository root. The local environment contains FastAPI, Uvicorn, OpenAI, python-dotenv, Pydantic, and their transitive dependencies. Dependency versions therefore cannot currently be reproduced reliably.

## Current problems and technical debt

- Importing `app.py` immediately requires an API key and starts an interactive loop, making testing and reuse difficult.
- Business logic, transport, presentation, configuration, and persistence are coupled in one file.
- `analytics.py` does not define the imported `log_interaction` function.
- Conversation state is global, process-local, and unavailable to multiple users or browser sessions.
- There is no request validation, consistent error contract, timeout policy at the API boundary, or rate limiting.
- Raw exception text is printed to users.
- No output validation or emergency-signal detection exists outside the prompt.
- The CLI has no web UI, accessibility model, responsive layout, or dashboard.
- There are no automated tests, health checks, structured logs, migration strategy, or reproducible setup instructions.
- `.env` protection should be verified and documented.

## Opportunities

- Extract configuration, safety, LLM, conversation, analytics, and persistence services.
- Add a FastAPI JSON/streaming API while preserving the CLI as an optional client.
- Use SQLite with a small schema for conversations, messages, and feedback.
- Add deterministic safety classification and response metadata around the LLM.
- Record privacy-conscious structured events and expose aggregate analytics.
- Add a React/TypeScript frontend with a calm, premium healthcare visual system.
- Add unit and API tests for validation, safety, persistence, and failure behavior.

## Recommended target architecture

```text
React + TypeScript frontend
        |
        | JSON / SSE
        v
FastAPI application
  ├── routers (chat, conversations, analytics, health)
  ├── services (LLM, safety, conversations, analytics)
  ├── database (SQLite + SQLAlchemy)
  └── configuration / structured logging
        |
        ├── OpenRouter-compatible model provider
        └── SQLite database
```

The first production-quality increment should keep deployment simple: one FastAPI process, SQLite for local persistence, an optional static frontend build, and provider credentials available only on the server.

## Risks

- Health-information responses require conservative safety messaging and must not imply diagnosis or treatment.
- Streaming increases implementation and test complexity.
- SQLite is appropriate for an initial portfolio product but should be isolated behind repositories for a future hosted database.
- Analytics must avoid storing unnecessary sensitive health content.

## Audit conclusion

The existing prototype is a useful LLM proof of concept but not yet a web product. The safest path is incremental extraction into a tested backend, followed by a frontend and analytics surfaces, while retaining the original safety intent and avoiding destructive replacement of the CLI behavior.
