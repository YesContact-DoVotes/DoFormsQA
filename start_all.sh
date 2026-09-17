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

# 1. Start Sample Target Web App (Port 3088)
echo "🌐 [1/3] Serving Sample Target App on http://localhost:3088 ..."
python3 -m http.server 3088 --directory sample_app &
SAMPLE_PID=$!

# 2. Start FastAPI QA Backend (Port 8080)
echo "🚀 [2/3] Starting FastAPI QA Backend on http://localhost:8080 ..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!

# 3. Start Next.js QA Frontend (Port 3090)
echo "💻 [3/3] Starting Next.js QA UI on http://localhost:3090 ..."
cd frontend && npm run dev -- -p 3090 &
FRONTEND_PID=$!

echo "=================================================="
echo "✅ All QA services running!"
echo "   - QA Frontend UI:   http://localhost:3090"
echo "   - QA Backend API:   http://localhost:8080/docs"
echo "   - Sample App Demo:  http://localhost:3088"
echo "=================================================="
echo "Press CTRL+C to stop all servers."

trap "kill $SAMPLE_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" INT TERM
wait
