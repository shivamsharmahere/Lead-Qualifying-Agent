import uuid
from sqlalchemy import Column, String, Float, Integer, Enum, DateTime, ForeignKey, Index, func, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db import Base
import enum

class PriorityEnum(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    pending = "pending"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    budget = Column(Float, nullable=True) # Storing as Float/NUMERIC in INR
    preference = Column(String, nullable=True)
    timeline_months = Column(Integer, nullable=True)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.pending, nullable=False)
    raw_data = Column(JSONB, nullable=True)
    follow_up_count = Column(Integer, default=0, nullable=False)
    follow_up_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
