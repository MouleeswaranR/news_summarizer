import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def _run_scheduled_fetch():
    """Fetch all categories and update cache."""
    from config import VALID_CATEGORIES, VALID_REGIONS
    from graph import build_graph
    from database import init_db
    from cache_manager import save_to_cache
    import time

    init_db()
    graph = build_graph()

    for category in VALID_CATEGORIES:
        for region in VALID_REGIONS:
            try:
                state = {
                    "messages": [],
                    "category": category,
                    "region": region,
                    "date": "",
                    "raw_articles": [],
                    "filtered_articles": [],
                    "summaries": [],
                    "audio_file": None,
                    "error": None,
                }
                result = graph.invoke(state)
                if result.get("summaries"):
                    save_to_cache(category, region, result["summaries"])
            except Exception:
                pass
            time.sleep(3)


@st.cache_resource
def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_scheduled_fetch,
        CronTrigger(hour="8,13,20", minute=0, timezone=IST),
        id="news_fetch",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
