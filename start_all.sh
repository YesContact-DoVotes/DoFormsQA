#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================="
echo "⚡ Starting AI QA Agent Platform"
echo "=================================================="

# Activate virtualenv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 1. Start Sample Target Web App (Port 3000)
echo "🌐 [1/3] Serving Sample Target App on http://localhost:3000 ..."
python3 -m http.server 3000 --directory sample_app &
SAMPLE_PID=$!

# 2. Start FastAPI Backend (Port 8000)
echo "🚀 [2/3] Starting FastAPI Backend on http://localhost:8000 ..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 3. Start Next.js Frontend (Port 3001)
echo "💻 [3/3] Starting Next.js UI on http://localhost:3001 ..."
cd frontend && npm run dev -- -p 3001 &
FRONTEND_PID=$!

echo "=================================================="
echo "✅ All services running!"
echo "   - Frontend UI:  http://localhost:3001"
echo "   - Backend API:  http://localhost:8000/docs"
echo "   - Sample App:   http://localhost:3000"
echo "=================================================="
echo "Press CTRL+C to stop all servers."

trap "kill $SAMPLE_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" INT TERM
wait
