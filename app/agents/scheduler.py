import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.agents.ceo_agent import run_ceo_agent
from app.agents.intelligence_agent import run_intelligence_agent
from app.agents.marketing_agent import run_marketing_agent
from app.agents.operations_agent import run_operations_agent
from app.agents.sales_agent import run_sales_agent

logger = logging.getLogger(__name__)

TIMEZONE = "Asia/Bangkok"


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Sales Agent — daily 09:00 Bangkok
    scheduler.add_job(
        run_sales_agent,
        CronTrigger(hour=9, minute=0, timezone=TIMEZONE),
        id="sales_agent",
        name="Sales Follow-Up Agent",
        replace_existing=True,
    )

    # Intelligence Agent — every Monday 08:00 Bangkok
    scheduler.add_job(
        run_intelligence_agent,
        CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=TIMEZONE),
        id="intelligence_agent",
        name="Competitor Intelligence Agent",
        replace_existing=True,
    )

    # CEO Agent — every Monday 08:30 Bangkok
    scheduler.add_job(
        run_ceo_agent,
        CronTrigger(day_of_week="mon", hour=8, minute=30, timezone=TIMEZONE),
        id="ceo_agent",
        name="CEO Weekly Memo Agent",
        replace_existing=True,
    )

    # Operations Agent — daily 08:00 Bangkok
    scheduler.add_job(
        run_operations_agent,
        CronTrigger(hour=8, minute=0, timezone=TIMEZONE),
        id="operations_agent",
        name="Operations Stock Alert Agent",
        replace_existing=True,
    )

    # Marketing Agent — every Monday 09:00 Bangkok
    scheduler.add_job(
        run_marketing_agent,
        CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=TIMEZONE),
        id="marketing_agent",
        name="Marketing Content Agent",
        replace_existing=True,
    )

    return scheduler
