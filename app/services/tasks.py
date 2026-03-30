import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.db import AsyncSessionLocal
from app.services.followup import process_follow_ups

logger = logging.getLogger(__name__)


async def scheduled_follow_up_job():
    logger.info("Starting scheduled follow-up job...")
    async with AsyncSessionLocal() as db:
        try:
            await process_follow_ups(db)
        except Exception as e:
            logger.error(f"Error in follow-up job: {e}")
    logger.info("Completed scheduled follow-up job.")


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_follow_up_job, "interval", minutes=15, id="follow_up_job"
    )
    return scheduler
