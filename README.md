# 🤖 AI QA Agent (MVP)

> **Автономный E2E и exploratory инструмент тестирования web-приложений на базе AI и Playwright.**

Система принимает URL любого веб-приложения, текстовую цель тестирования (mission) и опционально требования (PRD / MVP), после чего автономно исследует приложение, формирует сценарии, выполняет действия в браузере, отслеживает ошибки консоли и сети, выявляет и перепроверяет баги, генерирует итоговый QA-отчет (`report.md`) и создает Playwright regression-тесты.

---

## 🌟 Ключевые возможности

- 🚀 **Автономный Exploratory & E2E цикл**: не требует ручного написания шагов перед запуском.
- 🧠 **AI Roles & Subsystems**:
  - **Discovery**: исследование интерфейса и выявление областей приложения (Authentication, Form Builder, Navigation и др.).
  - **Planner**: составление и приоритизация 10–30 тест-сценариев (Happy paths, Negative testing, Persistence, Navigation).
  - **Executor**: принятие решений по действиям на основе компактного DOM-снимка и истории.
  - **Analyzer**: выявление аномалий, 4xx/5xx ошибок, console.error и защита от зацикливания (Loop Prevention).
  - **Bug Verifier**: повторная изолированная проверка потенциального бага (минимум 2 попытки) перед подтверждением (`CONFIRMED` / `REJECTED`).
  - **Reporter**: генерация отчета `report.md` со сводкой, покрытием по областям и доказательствами (evidence).
  - **Regression Generator**: синтез готовых Playwright `.spec.ts` тестов для разработчиков и CI/CD.
- 🌐 **Браузерная автоматизация (Playwright Chromium)**: поддержка живого (Headed) и фонового (Headless) режимов.
- ⚡ **Live WebSocket Dashboard**: real-time трансляция шагов, мыслей агента, статусов сценариев и находок.
- 🔌 **Мультипровайдер LLM**: поддержка OpenAI (GPT-4o / GPT-4o-mini / OpenRouter / Ollama), Google Gemini, а также встроенного **Mock AI Engine** для быстрого оффлайн-тестирования без API-ключей.

---

## 🏗️ Архитектура проекта

```text
DoFormsQA/
├── backend/                  # FastAPI + SQLAlchemy + Playwright + AI Engine
│   ├── app/
│   │   ├── api/              # REST Endpoints (/projects, /sessions) & WebSockets
│   │   ├── browser/          # Playwright Manager & DOM Snapshot parser
│   │   ├── llm/              # LLM Abstraction (OpenAI, Gemini, Mock)
│   │   ├── models/           # SQLAlchemy Models (Project, Session, Scenario, Step, Finding, Evidence, RegressionTest)
│   │   ├── qa/               # Discovery, Planner, Executor, Analyzer, Verifier, Reporter, Orchestrator
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── config.py         # Настройки приложения и бюджеты
│   │   ├── database.py       # Async SQLite / PostgreSQL сессии
│   │   └── main.py           # Точка входа FastAPI
│   ├── tests/                # Интеграционные и E2E тесты
│   └── requirements.txt
├── frontend/                 # Next.js 16 + TypeScript + Tailwind CSS
│   ├── app/                  # App Router (Проекты, Детали проекта, Live Session Control Room)
│   ├── components/           # UI компоненты (Navbar, Badges, Screenshot Lightbox)
│   └── lib/api.ts            # API и WebSocket клиент
├── sample_app/               # Тестовое веб-приложение DoForms для локальной проверки
│   ├── index.html            # Формы, конструктор вопросов, валидация, сохранение
│   └── MVP.md                # Пример требований
├── storage/                  # SQLite база данных, скриншоты, отчеты и сгенерированные тесты
├── start_all.sh              # Скрипт запуска всех сервисов одной командой
├── .env.example              # Шаблон конфигурации
└── .gitignore
```

---

## 🚀 Быстрый старт

### 1. Требования

- **Python**: 3.10+ (протестировано на 3.14)
- **Node.js**: 18+ (протестировано на 24)
- **Chromium / Playwright**

---

### 2. Установка и запуск одной командой (локально)

В корне проекта выполните:

```bash
./start_all.sh
```

Скрипт автоматически запустит:
1. 🌐 **Тестовое приложение (DoForms App)**: `http://localhost:3000`
2. 🚀 **Backend API**: `http://localhost:8000` (Документация Swagger: `http://localhost:8000/docs`)
3. 💻 **Frontend UI**: `http://localhost:3001`

---

### 3. Запуск через Docker Compose (в контейнерах)

Для запуска всех сервисов (Backend + Playwright Chromium, Frontend Next.js, Sample App) в Docker:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

---

### 4. Ручной запуск компонентов (опционально)

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

#### Тестовое приложение:
```bash
python3 -m http.server 3000 --directory sample_app
```

---

## ⚙️ Конфигурация (.env)

Скопируйте шаблон:
```bash
cp .env.example .env
```

Параметры:

```env
# Провайдер по умолчанию: mock (оффлайн), openai, gemini
DEFAULT_LLM_PROVIDER=mock

# OpenAI / OpenRouter / Ollama
OPENAI_API_KEY=your_openai_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Google Gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-1.5-pro

# Настройки браузера
DEFAULT_HEADLESS=false
BROWSER_VIEWPORT_WIDTH=1280
BROWSER_VIEWPORT_HEIGHT=800
ACTION_TIMEOUT_MS=8000

# База данных
DATABASE_URL=sqlite+aiosqlite:///storage/qa_agent.db
```

---

## 🧪 Запуск тестов

Для запуска полного набора юнит- и E2E-тестов оркестратора:

```bash
DEFAULT_HEADLESS=true PYTHONPATH=. ./venv/bin/pytest backend/tests/
```

---

## 📋 Пользовательский сценарий работы (E2E Flow)

1. Откройте веб-интерфейс `http://localhost:3001`.
2. Нажмите **"Create New Project"** (или **"Create Sample DoForms Project"** для автозаполнения).
3. Укажите URL приложения (`http://localhost:3000`) и нажмите **"Start QA Session"**.
4. Задайте Mission (цель тестирования) и бюджет действий (например, 100).
5. Нажмите **"START QA SESSION"**:
   - Агент запустит Chromium;
   - Проанализирует DOM и определит области приложения;
   - Составит тест-план со сценариями;
   - Проведет позитивные и негативные сценарии;
   - Зафиксирует и перепроверит баги;
   - Сгенерирует финальный отчет `report.md` и Playwright-тесты в реальном времени!

---

## 📄 Лицензия

MIT License
