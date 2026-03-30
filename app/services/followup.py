import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, null

from app.models.lead import Lead, PriorityEnum
from app.models.message import Message, RoleEnum
from app.services.message import add_message
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


def generate_follow_up_message(lead: Lead) -> str:
    """Generate personalized nudges based on turn number and priority."""
    name = lead.name or "there"
    loc = lead.preference or "properties"
    turn = lead.follow_up_count + 1

    if turn == 1:
        if lead.priority == PriorityEnum.high:
            return f"Hi {name}, given your timeline, I have some great {loc} options that could be a perfect fit. Shall we continue?"
        else:
            return f"Hi {name}, just checking in — are you still exploring {loc}? I'm happy to help!"

    elif turn == 2:
        return f"Hi {name}, just a friendly reminder — great properties around {loc} are moving quickly. Happy to share some options!"

    else:  # Turn 3 (Final)
        return f"This will be our last check-in, {name}. Feel free to reach out any time — we'd love to help you find your ideal property."


async def process_follow_ups(db: AsyncSession):
    """
    Find eligible leads and dispatch follow-ups.
    """
    now = datetime.now(timezone.utc)
    inactivity_threshold = now - timedelta(
        minutes=settings.FOLLOW_UP_INACTIVITY_MINUTES
    )
    cooldown_threshold = now - timedelta(hours=24)

    # Needs a lead where:
    # 1. follow_up_count < max allowed
    # 2. updated_at is older than inactivity threshold
    # 3. follow_up_sent_at is null OR older than 24 hours (cooldown)

    query = select(Lead).where(
        and_(
            Lead.follow_up_count < settings.FOLLOW_UP_MAX_COUNT,
            Lead.updated_at <= inactivity_threshold,
            or_(
                Lead.follow_up_sent_at == null(),
                Lead.follow_up_sent_at <= cooldown_threshold,
            ),
        )
    )

    result = await db.execute(query)
    eligible_leads = result.scalars().all()

    for lead in eligible_leads:
        # Check if the user has replied recently in the Messages table to avoid race conditions
        msg_query = select(Message).where(
            and_(
                Message.session_id == lead.session_id,
                Message.role == RoleEnum.user,
                Message.created_at > inactivity_threshold,
            )
        )
        recent_msgs = await db.execute(msg_query)
        if recent_msgs.scalars().first():
            logger.info(
                f"Skipping follow-up for {lead.session_id}, user replied recently."
            )
            continue

        # Dispatch Follow-Up
        msg_content = generate_follow_up_message(lead)

        # Save to history
        await add_message(db, lead.session_id, RoleEnum.assistant, msg_content)

        # Update lead
        lead.follow_up_count += 1
        lead.follow_up_sent_at = now
        db.add(lead)
        logger.info(
            f"Sent follow-up {lead.follow_up_count} to session {lead.session_id}"
        )

    await db.commit()
