"""
DoForms QA Agent - Quick Launcher Script
Starts FastAPI backend server on http://localhost:8000 and serves sample app.
"""
import uvicorn
from backend.app.main import app
from backend.app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.PROJECT_NAME} backend on http://0.0.0.0:8000 ...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
