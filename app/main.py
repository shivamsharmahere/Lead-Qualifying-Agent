from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.config import settings
from app.db import get_db
from app.api.webhook import router as webhook_router
from app.api.leads import router as leads_router
from app.api.reply import router as reply_router
from app.tasks import setup_scheduler

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
    description="Backend simulating a real estate AI chatbot that captures, qualifies, and manages leads.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(webhook_router)
app.include_router(leads_router)
app.include_router(reply_router)

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

    # Check if Groq API key is present as a basic health check
    llm_status = "configured" if settings.GROQ_API_KEY else "missing_api_key"

    return {
        "status": "ok",
        "db": db_status,
        "llm": llm_status
    }
