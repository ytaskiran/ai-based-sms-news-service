"""
Background scheduler for fetching news periodically
"""

import asyncio
import logging
from datetime import datetime
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .fetcher import fetch_news
from .sources import NEWS_SOURCES
from database.models import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsScheduler:
    """Schedules periodic news fetching jobs"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = get_db()
        self.categories = ['general', 'ai', 'tech']  # Excluding 'local' for now

    async def fetch_and_store_news(self, category: str):
        """
        Fetch news for a category and store in database

        Args:
            category: Category name
        """
        try:
            logger.info(f"Starting scheduled fetch for category: {category}")

            # Fetch articles from last 24 hours
            articles = fetch_news(category, hours=24)

            if articles:
                # Save to database
                self.db.save_articles(articles, category)
                logger.info(f"Successfully fetched and stored {len(articles)} articles for {category}")
            else:
                logger.warning(f"No articles fetched for {category}")

        except Exception as e:
            logger.error(f"Error in scheduled fetch for {category}: {e}")

    async def fetch_all_categories(self):
        """Fetch news for all categories"""
        logger.info("Starting scheduled fetch for all categories")

        tasks = [
            self.fetch_and_store_news(category)
            for category in self.categories
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Completed scheduled fetch for all categories")

    def start(self):
        """Start the scheduler with configured jobs"""

        # Fetch all news every 4 hours
        self.scheduler.add_job(
            self.fetch_all_categories,
            CronTrigger(hour='*/4'),  # Every 4 hours
            id='fetch_all_news',
            name='Fetch all news categories',
            replace_existing=True
        )

        # Morning briefing (8 AM)
        self.scheduler.add_job(
            self.fetch_all_categories,
            CronTrigger(hour=8, minute=0),
            id='morning_briefing',
            name='Morning news briefing',
            replace_existing=True
        )

        # Evening briefing (6 PM)
        self.scheduler.add_job(
            self.fetch_all_categories,
            CronTrigger(hour=18, minute=0),
            id='evening_briefing',
            name='Evening news briefing',
            replace_existing=True
        )

        # Cleanup old articles (daily at 3 AM)
        self.scheduler.add_job(
            self.cleanup_old_articles,
            CronTrigger(hour=3, minute=0),
            id='cleanup_articles',
            name='Cleanup old articles',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("News scheduler started successfully")

    async def cleanup_old_articles(self):
        """Clean up articles older than 7 days"""
        try:
            logger.info("Running cleanup of old articles")
            self.db.clear_old_articles(days=7)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("News scheduler stopped")

    async def fetch_now(self, category: str = None):
        """
        Manually trigger a news fetch

        Args:
            category: Specific category to fetch, or None for all
        """
        if category:
            await self.fetch_and_store_news(category)
        else:
            await self.fetch_all_categories()


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> NewsScheduler:
    """Get or create scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = NewsScheduler()
    return _scheduler_instance


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler
