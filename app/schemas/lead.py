import uuid
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.lead import PriorityEnum

class LeadBase(BaseModel):
    name: Optional[str] = None
    budget: Optional[float] = None
    preference: Optional[str] = None
    timeline_months: Optional[int] = None
    priority: PriorityEnum = PriorityEnum.pending

class LeadCreate(LeadBase):
    session_id: str

class LeadResponse(LeadBase):
    id: uuid.UUID
    session_id: str
    raw_data: Optional[Dict[str, Any]] = None
    follow_up_count: int
    follow_up_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LeadPaginationResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    size: int
