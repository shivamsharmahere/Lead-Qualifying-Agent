import uuid
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.message import RoleEnum


class MessageBase(BaseModel):
    role: RoleEnum
    content: str


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
    session_id: Optional[str] = Field(
        default=None, description="Auto-generated if not provided"
    )
    message: str = Field(..., description="User's message to the chatbot")
    metadata: Optional[dict] = Field(default=None, description="Optional metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "session_abc123",
                    "message": "Hi, I want to develop a WordPress website",
                },
                {"message": "I'm looking for a 3BHK apartment in Bangalore"},
            ]
        }
    }


class WebhookResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier for the conversation")
    reply: str = Field(..., description="AI's response message")
    lead_extracted: bool = Field(..., description="Whether lead info was extracted")
    lead_priority: Optional[str] = Field(
        default=None, description="Lead priority: high, medium, low, pending"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "session_abc123",
                    "reply": "Hi, this is Alex. I help people with software development, finding apartments and flats, buying cars, and various other services. How can I help you today?",
                    "lead_extracted": False,
                    "lead_priority": None,
                }
            ]
        }
    }
