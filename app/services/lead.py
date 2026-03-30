import logging
import re
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.lead import Lead, PriorityEnum
from app.services.scoring import score_lead

logger = logging.getLogger(__name__)


def parse_timeline(timeline_raw: Any) -> Optional[int]:
    """Parse timeline from various formats to months."""
    if timeline_raw is None:
        return None

    timeline_str = str(timeline_raw).lower().strip()

    if not timeline_str or timeline_str == "null":
        return None

    if any(x in timeline_str for x in ["asap", "urgent", "immediately", "right away"]):
        return 1

    match = re.search(r"(\d+)\s*(month|year|week|day)", timeline_str)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if "week" in unit:
            return max(1, val // 4)
        elif "year" in unit:
            return val * 12
        elif "day" in unit:
            return max(1, val // 30)
        else:
            return val

    if timeline_str.isdigit():
        return int(timeline_str)

    if "within" in timeline_str:
        num_match = re.search(r"within\s*(\d+)", timeline_str)
        if num_match:
            return int(num_match.group(1))

    if "ready" in timeline_str or "immediate" in timeline_str:
        return 1

    return None


def parse_budget(budget_raw: Any) -> Optional[float]:
    """Parse budget from various formats to INR float."""
    if budget_raw is None:
        return None

    budget_str = str(budget_raw).replace(",", "").replace(" ", "").lower()

    if not budget_str or budget_str == "null":
        return None

    val_match = re.search(r"(\d+(?:\.\d+)?)", budget_str)
    if not val_match:
        return None

    val = float(val_match.group(1))

    if any(x in budget_str for x in ["lakh", "l"]):
        return val * 100000
    elif any(x in budget_str for x in ["cr", "crore"]):
        return val * 10000000
    elif any(x in budget_str for x in ["k", "thousand"]):
        return val * 1000
    else:
        return val


async def get_lead(db: AsyncSession, session_id: str) -> Optional[Lead]:
    query = select(Lead).where(Lead.session_id == session_id)
    result = await db.execute(query)
    return result.scalars().first()


async def upsert_lead(
    db: AsyncSession, session_id: str, extracted_data: Dict[str, Any]
) -> Lead:
    """
    Updates or creates a Lead record using the incrementally extracted fields.
    Recalculates score whenever fields merge.
    """
    lead = await get_lead(db, session_id)

    additional_fields = extracted_data.get("additional_fields", {})
    top_level = {k: v for k, v in extracted_data.items() if k != "additional_fields"}

    budget_raw = top_level.get("budget") or additional_fields.get("budget")
    timeline_raw = (
        top_level.get("timeline")
        or top_level.get("timeline_months")
        or additional_fields.get("timeline")
    )
    location_raw = top_level.get("location") or additional_fields.get("location")
    phone_raw = top_level.get("phone") or additional_fields.get("phone")
    service_interest_raw = top_level.get("service_interest") or additional_fields.get(
        "service_interest"
    )

    parsed_budget = parse_budget(budget_raw)
    parsed_timeline = parse_timeline(timeline_raw)

    if not lead:
        lead = Lead(
            session_id=session_id,
            name=top_level.get("name"),
            email=top_level.get("email"),
            phone=phone_raw,
            location=location_raw,
            service_interest=service_interest_raw,
            budget=parsed_budget,
            timeline_months=parsed_timeline,
            raw_data=extracted_data,
            additional_fields=additional_fields,
        )
        db.add(lead)
    else:
        lead.raw_data = extracted_data
        lead.additional_fields = additional_fields

        if top_level.get("name"):
            lead.name = top_level.get("name")
        if top_level.get("email"):
            lead.email = top_level.get("email")
        if phone_raw:
            lead.phone = phone_raw
        if location_raw:
            lead.location = location_raw
        if service_interest_raw:
            lead.service_interest = service_interest_raw
        if parsed_budget is not None:
            lead.budget = parsed_budget
        if parsed_timeline is not None:
            lead.timeline_months = parsed_timeline

    lead.priority = score_lead(lead.budget, lead.timeline_months)

    await db.commit()
    await db.refresh(lead)
    return lead


async def get_all_leads(
    db: AsyncSession, priority: str = None, limit: int = 20, offset: int = 0
):
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

    return {
        "items": leads,
        "total": total,
        "page": (offset // limit) + 1,
        "size": limit,
    }
