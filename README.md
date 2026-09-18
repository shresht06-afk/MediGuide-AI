# MediGuide AI 🩺

> A calm, professional AI health-information assistant powered by OpenRouter — not a doctor, but a knowledgeable guide.

MediGuide AI provides general educational health information through a conversational interface. It helps users understand symptoms, conditions, medications, nutrition, and wellness topics while automatically detecting emergency situations and directing users to professional care when needed.

---

## Features

- 🤖 **AI-Powered Chat** — Streams responses from any OpenRouter-compatible LLM
- 🚨 **Emergency Detection** — Pattern-matches for chest pain, stroke signs, self-harm signals, and other critical situations before sending anything to the LLM
- 🗂️ **Topic Classification** — Automatically tags conversations across Nutrition, Symptoms, Medication, Sleep & Wellness, and Mental Wellness
- 📊 **Analytics Dashboard** — Tracks interaction volume, response times, topic breakdowns, and feedback scores
- 💬 **Conversation History** — Persists full multi-turn conversations in a local SQLite database
- 👍 **User Feedback** — Thumbs up/down rating per AI response
- 🖥️ **Web UI** — Next.js 16 + React 19 frontend with Tailwind CSS
- 🔌 **REST API** — FastAPI backend with streaming support and CORS configuration
- 🖊️ **CLI Mode** — Run the chatbot directly in your terminal without the frontend

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, Uvicorn |
| AI Provider | OpenRouter (OpenAI-compatible API) |
| Database | SQLite (via built-in sqlite3) |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Config | python-dotenv |

---

## Project Structure

```
MediGuide-AI/
├── mediguide/               # Core Python package
│   ├── api.py               # FastAPI routes (REST + streaming)
│   ├── config.py            # Settings loaded from .env
│   ├── db.py                # SQLite database layer
│   ├── llm.py               # OpenRouter streaming client
│   ├── safety.py            # Emergency detection + system prompt
│   └── topics.py            # Topic classification
├── frontend/                # Next.js web application
│   ├── app/                 # App Router pages
│   ├── components/          # React components
│   └── lib/                 # API client utilities
├── analytics.py             # CLI analytics helper
├── analytics_engine.py      # Analytics aggregation logic
├── app.py                   # CLI entry point
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variable template
```

---

## Getting Started

### Prerequisites

- Python 3.12 or later
- Node.js 18 or later (for the web frontend)
- An [OpenRouter](https://openrouter.ai) API key

### 1. Clone the repository

```bash
git clone https://github.com/your-username/MediGuide-AI.git
cd MediGuide-AI
```

### 2. Set up the Python environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
OPENROUTER_API_KEY=your-openrouter-key
MEDIGUIDE_MODEL=openrouter/free        # or any model slug from openrouter.ai/models
MEDIGUIDE_DATABASE=mediguide.db
MEDIGUIDE_CORS_ORIGINS=http://localhost:3000
```

### 4. Start the backend

```bash
uvicorn mediguide.api:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## CLI Mode

You can chat with MediGuide directly in your terminal without starting any servers:

```bash
python app.py
```

```
MediGuide AI - general health information (type 'exit' to close)
You: What can cause a persistent headache?
MediGuide (1.43s): Persistent headaches can have many causes...
```

Type `exit` or `quit` to close the session.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/conversations` | Start a new conversation |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversations/{id}` | Get a conversation with messages |
| `POST` | `/api/conversations/{id}/messages` | Send a message and get a response |
| `POST` | `/api/messages/{id}/feedback` | Submit thumbs up/down feedback |
| `GET` | `/api/analytics/summary` | Get aggregated analytics metrics |

---

## Safety & Disclaimer

MediGuide AI is designed for **general educational purposes only**.

- It is **not a substitute for professional medical advice**, diagnosis, or treatment.
- Emergency keywords (chest pain, difficulty breathing, self-harm, etc.) are detected locally **before** any LLM call. Users are immediately directed to call emergency services.
- The AI is explicitly instructed never to diagnose, prescribe, invent measurements, or delay professional care in potentially serious situations.

**Always consult a qualified healthcare professional for medical concerns.**

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is open source. See [LICENSE](LICENSE) for details.
