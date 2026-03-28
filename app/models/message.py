import uuid
from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db import Base
import enum

class RoleEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=False, index=True) # Usually tied to a lead
    role = Column(Enum(RoleEnum), nullable=False)
    content = Column(Text, nullable=False)
    message_hash = Column(String(64), nullable=False)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('session_id', 'message_hash', name='uix_session_message_hash'),
    )
