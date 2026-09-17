import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.logging_config import setup_logging
from backend.app.api.projects import router as projects_router
from backend.app.api.sessions import router as sessions_router
from backend.app.api.websocket import ws_manager

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing QA Agent Database & System Services...")
    await init_db()
    logger.info("DoForms QA Backend ready and listening.")
    yield



app = FastAPI(
    title="AI QA Agent API",
    description="Autonomous E2E and Exploratory Testing System API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount storage directory for artifacts & screenshots
storage_dir = Path(settings.STORAGE_PATH)
storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

# Include API Routers
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(sessions_router, prefix=settings.API_V1_STR)


@app.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    await ws_manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive, listen for client pings or commands
            data = await websocket.receive_text()
            # Echo heartbeat if needed
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, session_id)
    except Exception:
        ws_manager.disconnect(websocket, session_id)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
