import uuid
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.message import RoleEnum

class MessageBase(BaseModel):
    role: RoleEnum
    content: str
    tokens_used: Optional[int] = None

class MessageCreate(MessageBase):
    session_id: str
    message_hash: str

class MessageResponse(MessageBase):
    id: uuid.UUID
    session_id: str
    message_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

class WebhookPayload(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Auto-generated if not provided")
    message: str
    metadata: Optional[dict] = None

class WebhookResponse(BaseModel):
    session_id: str
    reply: str
    lead_extracted: bool
    lead_priority: Optional[str]
    tokens_used: int
    cached: bool
