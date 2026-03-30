import subprocess
import sys
import os
import time
import argparse

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.db import get_db
from app.api.router import api_router
from app.services.tasks import setup_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = setup_scheduler()
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="AI-Powered Lead Capture Chatbot",
    description="Backend for lead capture chatbot with LLM-powered conversations",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "unknown"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    llm_status = "configured" if settings.GROQ_API_KEY else "missing_api_key"

    return {"status": "ok", "db": db_status, "llm": llm_status}


# ============= Runner Functions =============


def run_backend():
    print("🚀 Starting FastAPI backend on port 8000...")
    print("   (Use --reload to auto-reload on changes)")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ]
    )


def run_frontend():
    print("🚀 Starting Streamlit dashboard on port 8501...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "dashboard/main.py",
            "--server.port",
            "8501",
        ]
    )


def run_all():
    print("🚀 Starting AI-Powered Lead Capture Chatbot services...")

    # Start FastAPI server
    print("Starting FastAPI backend on port 8000 (with reload)...")
    fastapi_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    # Give the backend a second to initialize before starting the frontend
    time.sleep(2)

    # Start Streamlit dashboard
    print("Starting Streamlit dashboard on port 8501...")
    streamlit_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "dashboard/main.py",
            "--server.port",
            "8501",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    try:
        # Wait for both processes
        fastapi_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        fastapi_process.wait()
        streamlit_process.wait()
        print("Shutdown complete.")


def main():
    parser = argparse.ArgumentParser(description="Lead Capturing Bot")
    parser.add_argument("--b", action="store_true", help="Run only backend server")
    parser.add_argument(
        "--f", action="store_true", help="Run only frontend (Streamlit)"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run both backend and frontend (default)"
    )

    args = parser.parse_args()

    if args.b:
        run_backend()
    elif args.f:
        run_frontend()
    else:
        run_all()


if __name__ == "__main__":
    main()
