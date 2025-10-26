"""
Simple file-based database for storing articles and summaries
Using JSON for simplicity - can be migrated to SQLite/PostgreSQL later
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsDatabase:
    """Simple JSON-based database for articles and summaries"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.articles_file = self.data_dir / "articles.json"
        self.summaries_file = self.data_dir / "summaries.json"

        # Initialize files if they don't exist
        self._init_files()

    def _init_files(self):
        """Initialize database files if they don't exist"""
        if not self.articles_file.exists():
            self._write_json(self.articles_file, [])

        if not self.summaries_file.exists():
            self._write_json(self.summaries_file, {})

    def _read_json(self, file_path: Path) -> any:
        """Read JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return [] if file_path == self.articles_file else {}

    def _write_json(self, file_path: Path, data: any):
        """Write JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")

    def save_articles(self, articles: List[Dict], category: str):
        """
        Save articles to database

        Args:
            articles: List of article dictionaries
            category: Category name
        """
        existing_articles = self._read_json(self.articles_file)

        # Convert to list if not already
        if not isinstance(existing_articles, list):
            existing_articles = []

        # Add category and save timestamp to each article
        for article in articles:
            article['category'] = category
            article['saved_at'] = datetime.now().isoformat()
            # Ensure published is stored as ISO string
            if isinstance(article.get('published'), datetime):
                article['published'] = article['published'].isoformat()

            # Check if article already exists (by link)
            existing = any(a.get('link') == article.get('link') for a in existing_articles)
            if not existing:
                existing_articles.append(article)

        # Sort by published date (handle both datetime and string)
        def get_sort_key(x):
            pub = x.get('published', '')
            if isinstance(pub, str):
                return pub
            elif isinstance(pub, datetime):
                return pub.isoformat()
            return ''

        existing_articles.sort(key=get_sort_key, reverse=True)

        # Keep only last 1000 articles to prevent file from growing too large
        existing_articles = existing_articles[:1000]

        self._write_json(self.articles_file, existing_articles)
        logger.info(f"Saved {len(articles)} new articles for category: {category}")

    def get_articles(self, category: str, limit: int = 50) -> List[Dict]:
        """
        Get articles for a specific category

        Args:
            category: Category name
            limit: Maximum number of articles to return

        Returns:
            List of articles
        """
        all_articles = self._read_json(self.articles_file)

        # Filter by category
        category_articles = [
            a for a in all_articles
            if a.get('category') == category
        ]

        return category_articles[:limit]

    def save_summary(self, category: str, summary: str, articles_count: int):
        """
        Save generated summary to cache

        Args:
            category: Category name
            summary: Generated summary text
            articles_count: Number of articles summarized
        """
        summaries = self._read_json(self.summaries_file)

        summaries[category] = {
            "summary": summary,
            "generated_at": datetime.now().isoformat(),
            "articles_count": articles_count
        }

        self._write_json(self.summaries_file, summaries)
        logger.info(f"Saved summary for category: {category}")

    def get_summary(self, category: str, max_age_hours: int = 6) -> Optional[str]:
        """
        Get cached summary if it's fresh enough

        Args:
            category: Category name
            max_age_hours: Maximum age of summary in hours

        Returns:
            Summary text if fresh, None otherwise
        """
        summaries = self._read_json(self.summaries_file)

        if category not in summaries:
            return None

        summary_data = summaries[category]
        generated_at = datetime.fromisoformat(summary_data['generated_at'])

        # Check if summary is still fresh
        age_hours = (datetime.now() - generated_at).total_seconds() / 3600

        if age_hours <= max_age_hours:
            logger.info(f"Using cached summary for {category} (age: {age_hours:.1f}h)")
            return summary_data['summary']

        logger.info(f"Cached summary for {category} is too old ({age_hours:.1f}h)")
        return None

    def clear_old_articles(self, days: int = 7):
        """
        Remove articles older than specified days

        Args:
            days: Number of days to keep
        """
        articles = self._read_json(self.articles_file)

        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        filtered_articles = [
            a for a in articles
            if datetime.fromisoformat(a.get('saved_at', datetime.now().isoformat())).timestamp() > cutoff_date
        ]

        removed_count = len(articles) - len(filtered_articles)
        self._write_json(self.articles_file, filtered_articles)

        logger.info(f"Removed {removed_count} old articles")


# Global database instance
_db_instance = None


def get_db() -> NewsDatabase:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = NewsDatabase()
    return _db_instance
