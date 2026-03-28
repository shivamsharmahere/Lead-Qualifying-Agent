from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db import get_db
from app.schemas.lead import LeadPaginationResponse
from app.services.lead import get_all_leads

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.get("", response_model=LeadPaginationResponse)
async def list_leads(
    priority: Optional[str] = Query(None, description="Filter by priority: high, medium, low, pending"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a paginated, filterable list of all captured leads.
    """
    result = await get_all_leads(db, priority, limit, offset)
    return result
