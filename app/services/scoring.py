import logging
from app.models.lead import PriorityEnum
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


def score_lead(budget: float = None, timeline_months: int = None) -> PriorityEnum:
    """
    Evaluates the lead priority based on extracted fields.
    Rules loaded from environment configuration.
    """
    if budget is None and timeline_months is None:
        return PriorityEnum.pending

    budget = budget or 0
    timeline_months = timeline_months or 999

    # HIGH | Budget >= 70L AND timeline <= 3 months
    if (
        budget >= settings.HIGH_PRIORITY_BUDGET_INR
        and timeline_months <= settings.HIGH_PRIORITY_TIMELINE_MONTHS
    ):
        return PriorityEnum.high

    # HIGH | Budget >= 1Cr (any timeline)
    if budget >= 10_000_000:
        return PriorityEnum.high

    # MEDIUM | Budget >= 30L AND timeline <= 6 months
    if budget >= 3_000_000 and timeline_months <= 6:
        return PriorityEnum.medium

    # MEDIUM | Budget >= 70L AND timeline > 3 months
    if (
        budget >= settings.HIGH_PRIORITY_BUDGET_INR
        and timeline_months > settings.HIGH_PRIORITY_TIMELINE_MONTHS
    ):
        return PriorityEnum.medium

    # LOW | All other combinations
    return PriorityEnum.low
