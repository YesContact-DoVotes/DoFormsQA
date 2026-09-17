# 🤖 AI QA Agent (MVP)

> **Autonomous E2E and exploratory web application testing platform powered by AI and Playwright.**

The AI QA Agent takes any web application URL, a natural-language testing mission, and optional requirements (PRD / MVP document). It autonomously explores the application, discovers functional areas, generates prioritized test scenarios, executes browser actions, tracks console and network errors, detects and verifies findings, produces comprehensive QA reports (`report.md`), and synthesizes Playwright regression test specifications.

---

## 🌟 Key Features

- 🚀 **Autonomous Exploratory & E2E Lifecycle**: No need to manually script tests in advance.
- 🧠 **Modular AI Roles & Subsystems**:
  - **Discovery**: Analyzes entry DOM and extracts core application areas (Authentication, Form Builder, Navigation, etc.).
  - **Planner**: Plans and prioritizes 10–30 test scenarios (Happy paths, Negative input validation, State persistence, UI consistency).
  - **Executor**: Decides atomic browser actions using compact DOM snapshots and recent action history.
  - **Analyzer**: Detects anomalies, HTTP 4xx/5xx API failures, `console.error` logs, and prevents infinite loops (Loop Prevention: 3+ repeat trigger).
  - **Bug Verifier**: Re-executes potential findings in isolated replay runs (minimum 2 attempts) before updating status (`CONFIRMED` or `REJECTED`).
  - **Reporter**: Compiles structured Markdown QA reports (`report.md`) with area coverage statistics, executive summaries, and evidence attachments.
  - **Regression Generator**: Synthesizes standalone Playwright TypeScript (`.spec.ts`) regression tests ready for CI/CD pipelines.
- 🌐 **Browser Automation (Playwright Chromium)**: Supports interactive headed browser sessions and headless execution.
- ⚡ **Real-Time Live Dashboard**: WebSocket streaming of executed actions, AI agent thought bubbles, scenario statuses, and findings.
- 🔌 **LLM Provider**: Native integration with **OpenAI Codex Sandbox** (`openai-codex`), OpenAI (GPT-4o), and Google Gemini.

---

## 🏗️ Project Architecture

```text
DoFormsQA/
├── backend/                  # FastAPI + SQLAlchemy + Playwright + AI Engine
│   ├── app/
│   │   ├── api/              # REST Endpoints (/projects, /sessions) & WebSockets
│   │   ├── browser/          # Playwright Manager & DOM Snapshot parser
│   │   ├── llm/              # LLM Abstraction (Codex Sandbox, OpenAI, Gemini)
│   │   ├── models/           # SQLAlchemy Models (Project, Session, Scenario, Step, Finding, Evidence, RegressionTest)
│   │   ├── qa/               # Discovery, Planner, Executor, Analyzer, Verifier, Reporter, Orchestrator
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── config.py         # Application settings and limits
│   │   ├── database.py       # Async SQLite / PostgreSQL session setup
│   │   └── main.py           # FastAPI entrypoint
│   ├── tests/                # Integration and full E2E orchestrator tests
│   └── requirements.txt
├── frontend/                 # Next.js 16 + TypeScript + Tailwind CSS
│   ├── app/                  # App Router (Projects, Project View, Live Session Control Room)
│   ├── components/           # UI Components (Navbar, Badges, Screenshot Lightbox)
│   └── lib/api.ts            # API and WebSocket client
├── sample_app/               # Sample DoForms target web app for local testing
│   ├── index.html            # Forms, questions builder, validation, persistence
│   └── MVP.md                # Sample requirements document
├── deploy/                   # Docker & Docker Compose setup
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   └── README.md
├── storage/                  # SQLite DB, screenshots, reports, and generated regression tests
├── start_all.sh              # Single-command local launcher
├── .env.example              # Environment variables template
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python**: 3.10+ (tested with 3.14)
- **Node.js**: 18+ (tested with 24)
- **Chromium / Playwright**

---

### 2. Single-Command Local Launch

Run the startup script in the project root:

```bash
./start_all.sh
```

This launches all three services:
1. 🌐 **Sample Target Web App (DoForms)**: `http://localhost:3000`
2. 🚀 **FastAPI Backend**: `http://localhost:8000` (Swagger Docs: `http://localhost:8000/docs`)
3. 💻 **Next.js Frontend UI**: `http://localhost:3001`

---

### 3. Docker Compose Launch (Containerized)

To build and run all services in isolated Docker containers:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

---

### 4. Manual Component Launch (Optional)

#### Backend:
```bash
source venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend:
```bash
cd frontend
npm run dev -- -p 3001
```

#### Sample Target Web App:
```bash
python3 -m http.server 3000 --directory sample_app
```

---

## ⚙️ Configuration (.env)

Copy the environment template:
```bash
cp .env.example .env
```

Available options:

```env
# Default Provider: codex, openai, gemini
DEFAULT_LLM_PROVIDER=codex

# OpenAI / OpenRouter / Ollama
OPENAI_API_KEY=your_openai_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Google Gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-1.5-pro

# Browser Automation
DEFAULT_HEADLESS=false
BROWSER_VIEWPORT_WIDTH=1280
BROWSER_VIEWPORT_HEIGHT=800
ACTION_TIMEOUT_MS=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///storage/qa_agent.db
```

---

## 🧪 Running Automated Tests

Run the complete test suite (unit + full autonomous E2E orchestrator test):

```bash
DEFAULT_HEADLESS=true PYTHONPATH=. ./venv/bin/pytest backend/tests/
```

---

## 📋 Typical User Flow

1. Open the web interface at `http://localhost:3001`.
2. Click **"Create New Project"** (or click **"Create Sample DoForms Project"** to auto-fill requirements).
3. Specify your application URL (`http://localhost:3000`) and click **"Start QA Session"**.
4. Configure the testing mission directive and action budget (e.g. 100 actions).
5. Click **"START QA SESSION"**:
   - The agent launches Chromium;
   - Discovers application structure and form entry points;
   - Builds a prioritized test plan;
   - Executes exploratory actions and negative validations;
   - Detects and re-verifies bugs;
   - Compiles a final `report.md` and generates Playwright regression tests in real-time.

---

## 📄 License

MIT License
