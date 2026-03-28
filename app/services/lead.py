import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.lead import Lead, PriorityEnum
from app.services.scoring import score_lead

logger = logging.getLogger(__name__)

async def get_lead(db: AsyncSession, session_id: str) -> Optional[Lead]:
    query = select(Lead).where(Lead.session_id == session_id)
    result = await db.execute(query)
    return result.scalars().first()

async def upsert_lead(
    db: AsyncSession, 
    session_id: str, 
    extracted_data: Dict[str, Any]
) -> Lead:
    """
    Updates or creates a Lead record using the incrementally extracted fields.
    Recalculates score whenever fields merge.
    """
    lead = await get_lead(db, session_id)
    
    # Clean the extracted data: ensure numerical fields are properly typed
    budget_raw = extracted_data.get("budget")
    timeline_raw = extracted_data.get("timeline_months")
    
    parsed_budget = None
    if budget_raw is not None:
        try: 
            parsed_budget = float(str(budget_raw).replace(",", "").replace(" ", "").replace("L", "00000").replace("lakhs","00000"))
            # Rough normalization if model outputs weird strings
            if "Cr" in str(budget_raw):
                parsed_budget = float(str(budget_raw).replace("Cr", "")) * 1_000_000_0
        except: 
            parsed_budget = None
            
    parsed_timeline = None
    if timeline_raw is not None:
        try: parsed_timeline = int(timeline_raw)
        except: parsed_timeline = None

    if not lead:
        # Create new
        lead = Lead(
            session_id=session_id,
            name=extracted_data.get("name"),
            budget=parsed_budget,
            preference=extracted_data.get("preference"),
            timeline_months=parsed_timeline,
            raw_data=extracted_data
        )
        db.add(lead)
    else:
        # Merge dictionaries for raw_data
        current_raw = dict(lead.raw_data or {})
        current_raw.update(extracted_data)
        lead.raw_data = current_raw
        
        # Additive updates: only overwrite if new data exists
        if extracted_data.get("name"): lead.name = extracted_data.get("name")
        if parsed_budget is not None: lead.budget = parsed_budget
        if extracted_data.get("preference"): lead.preference = extracted_data.get("preference")
        if parsed_timeline is not None: lead.timeline_months = parsed_timeline

    # Update Priority
    lead.priority = score_lead(lead.budget, lead.timeline_months)
    
    await db.commit()
    await db.refresh(lead)
    return lead

async def get_all_leads(db: AsyncSession, priority: str = None, limit: int = 20, offset: int = 0):
    query = select(Lead)
    if priority:
        query = query.where(Lead.priority == priority)
    
    query = query.order_by(Lead.updated_at.desc()).limit(limit).offset(offset)
    
    # Get total count (simple approach)
    from sqlalchemy import func
    count_query = select(func.count(Lead.id))
    if priority:
        count_query = count_query.where(Lead.priority == priority)
        
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    leads_result = await db.execute(query)
    leads = leads_result.scalars().all()
    
    return {"items": leads, "total": total, "page": (offset // limit) + 1, "size": limit}
