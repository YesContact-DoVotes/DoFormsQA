# 🐳 Docker Deployment Guide

Инструкция по запуску AI QA Agent в изолированном Docker-окружении.

---

## 🚀 Быстрый запуск через Docker Compose

Из корня проекта выполните:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Или в фоновом режиме:

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

---

## 🌐 Доступные сервисы

| Сервис | URL | Назначение |
| :--- | :--- | :--- |
| **Frontend UI** | [http://localhost:3001](http://localhost:3001) | Веб-интерфейс управления проектами и сессиями |
| **Backend API** | [http://localhost:8000/docs](http://localhost:8000/docs) | FastAPI Swagger API документация |
| **Sample Target App** | [http://localhost:3000](http://localhost:3000) | Тестовое веб-приложение DoForms для проверок |

---

## ⚙️ Переменные окружения

Вы можете настроить параметры в файле `.env` в корне проекта перед сборкой контейнеров:

```env
DEFAULT_LLM_PROVIDER=codex   # или openai / gemini
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

---

## 🛑 Остановка сервисов

```bash
docker compose -f deploy/docker-compose.yml down
```
