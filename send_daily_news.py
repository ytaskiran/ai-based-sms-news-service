#!/usr/bin/env python3
"""
Daily News SMS Sender
Fetches news, generates AI summaries, and sends to subscribers
Designed to run as a daily cron job
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

from news_aggregator.fetcher import NewsFetcher
from news_aggregator.sources import get_sources_by_category
from ai_summarizer import NewsSummarizer
from sms_service import SMSService

# Load environment variables
load_dotenv()

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "daily_news.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class DailyNewsService:
    """Orchestrates daily news fetching, summarization, and SMS delivery"""

    def __init__(self, subscribers_file: str = "subscribers.json", test_mode: bool = False):
        """
        Initialize the daily news service

        Args:
            subscribers_file: Path to JSON file with subscriber phone numbers
            test_mode: If True, don't send real SMS (dry-run mode)
        """
        self.subscribers_file = Path(subscribers_file)
        self.test_mode = test_mode
        self.news_fetcher = NewsFetcher()
        self.summarizer = NewsSummarizer()
        self.sms_service = SMSService(dry_run=test_mode)

        # In-memory cache for this execution
        self.articles_cache = {}
        self.summaries_cache = {}

    def load_subscribers(self) -> List[str]:
        """
        Load subscriber phone numbers from JSON file

        Returns:
            List of phone numbers
        """
        if not self.subscribers_file.exists():
            logger.error(f"Subscribers file not found: {self.subscribers_file}")
            return []

        try:
            with open(self.subscribers_file, 'r') as f:
                data = json.load(f)
                subscribers = data.get('subscribers', [])
                logger.info(f"Loaded {len(subscribers)} subscribers")
                return subscribers
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
            return []

    def fetch_news_for_category(self, category: str) -> List[Dict]:
        """
        Fetch news articles for a specific category

        Args:
            category: Category name (general, ai, tech, local)

        Returns:
            List of articles
        """
        logger.info(f"Fetching news for category: {category}")
        sources = get_sources_by_category(category)
        if not sources:
            logger.warning(f"No sources configured for category: {category}")
            return []

        articles = self.news_fetcher.fetch_recent_articles(sources, hours=24)
        logger.info(f"Fetched {len(articles)} articles for {category}")

        return articles

    def fetch_all_news(self) -> Dict[str, List[Dict]]:
        """
        Fetch news for all categories

        Returns:
            Dict mapping category names to article lists
        """
        categories = ["general", "ai", "tech", "local"]
        logger.info("Fetching news for all categories...")
        for category in categories:
            self.articles_cache[category] = self.fetch_news_for_category(category)

        total_articles = sum(len(articles) for articles in self.articles_cache.values())
        logger.info(f"Fetched total of {total_articles} articles across all categories")

        return self.articles_cache

    def generate_summaries(self) -> Dict[str, str]:
        """
        Generate AI summaries for all categories

        Returns:
            Dict mapping category names to summary text
        """
        logger.info("Generating AI summaries for all categories...")

        for category, articles in self.articles_cache.items():
            if not articles:
                logger.info(f"No articles for {category}, skipping summary")
                continue

            try:
                summary = self.summarizer.summarize_articles(articles, category)
                self.summaries_cache[category] = summary
                logger.info(f"Generated summary for {category} ({len(summary)} chars)")
            except Exception as e:
                logger.error(f"Error generating summary for {category}: {e}")
                # Create fallback summary
                self.summaries_cache[category] = self._create_fallback_summary(articles, category)

        return self.summaries_cache

    def _create_fallback_summary(self, articles: List[Dict], category: str) -> str:
        """Create simple fallback if AI summary fails"""
        category_labels = {
            "general": "GENERAL NEWS",
            "ai": "AI NEWS",
            "tech": "TECH NEWS",
            "local": "LOCAL NEWS"
        }

        label = category_labels.get(category, "NEWS")
        summary = f"{label}\n\n"

        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', 'No title')[:80]
            summary += f"{i}. {title}\n"

        return summary

    def create_daily_briefing(self) -> str:
        """
        Create complete daily briefing with all categories

        Returns:
            Complete briefing text
        """
        logger.info("Creating daily briefing...")

        briefing = f"DAILY NEWS BRIEFING\n{datetime.now().strftime('%B %d, %Y')}\n"
        briefing += "=" * 40 + "\n\n"

        categories = [
            ("general", "WORLD NEWS"),
            ("ai", "AI & MACHINE LEARNING"),
            ("tech", "TECHNOLOGY"),
            ("local", "LOCAL NEWS")
        ]

        for category, label in categories:
            if category not in self.summaries_cache or not self.summaries_cache[category]:
                continue

            summary = self.summaries_cache[category]

            # Add category header if not already in summary
            if label not in summary:
                briefing += f"\n{label}\n{'-' * len(label)}\n"

            briefing += f"{summary}\n\n"

        briefing += "=" * 40 + "\n"
        briefing += "Stay informed! Reply STOP to unsubscribe."

        logger.info(f"Daily briefing created ({len(briefing)} chars)")

        return briefing

    def send_to_subscribers(self, message: str, subscribers: List[str]) -> Dict:
        """
        Send message to all subscribers

        Args:
            message: Message text to send
            subscribers: List of phone numbers

        Returns:
            Results dict with success/failure counts
        """
        if not subscribers:
            logger.warning("No subscribers to send to")
            return {"total": 0, "successful": 0, "failed": 0, "details": []}

        logger.info(f"Sending news to {len(subscribers)} subscribers...")

        results = self.sms_service.send_bulk_sms(
            recipients=subscribers,
            message=message,
            max_retries=5
        )

        logger.info(f"SMS delivery complete: {results['successful']} sent, {results['failed']} failed")

        # Log failures
        for result in results['details']:
            if not result['success']:
                logger.error(f"Failed to send to {result['to']}: {result.get('error', 'Unknown error')}")

        return results

    def run(self):
        """
        Main execution: fetch news, generate summaries, send to subscribers
        """
        logger.info("=" * 60)
        logger.info(f"Starting daily news service - {datetime.now()}")
        if self.test_mode:
            logger.info("**TEST MODE ENABLED** - No real SMS will be sent")
        logger.info("=" * 60)

        try:
            # 1. Load subscribers
            subscribers = self.load_subscribers()

            if not subscribers:
                logger.error("No subscribers found. Exiting.")
                return

            # 2. Fetch news for all categories
            self.fetch_all_news()

            # 3. Generate AI summaries
            self.generate_summaries()

            # 4. Create daily briefing
            briefing = self.create_daily_briefing()

            # 5. Send to subscribers
            results = self.send_to_subscribers(briefing, subscribers)

            # 6. Log summary
            logger.info("=" * 60)
            logger.info("DAILY NEWS SERVICE COMPLETE")
            logger.info(f"Total subscribers: {len(subscribers)}")
            logger.info(f"Successfully sent: {results['successful']}")
            logger.info(f"Failed: {results['failed']}")
            logger.info(f"Briefing length: {len(briefing)} characters")
            logger.info("=" * 60)

            # 7. Clear cache (in-memory, so happens automatically at script end)
            self.articles_cache.clear()
            self.summaries_cache.clear()

        except Exception as e:
            logger.error(f"Fatal error in daily news service: {e}", exc_info=True)
            sys.exit(1)


def main():
    """Entry point for the script"""
    parser = argparse.ArgumentParser(
        description='Daily News SMS Service - Fetches news, generates AI summaries, and sends to subscribers'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: fetch news and generate summaries but don\'t send real SMS messages'
    )

    args = parser.parse_args()

    service = DailyNewsService(test_mode=args.test)
    service.run()


if __name__ == "__main__":
    main()
