from fastapi import APIRouter
from app.api.endpoints import webhook, leads, reply

api_router = APIRouter()

api_router.include_router(webhook.router, prefix="/webhook", tags=["Chat"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(reply.router, prefix="/reply", tags=["Conversation"])
