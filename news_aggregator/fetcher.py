"""
RSS feed fetcher for news aggregation
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches and parses RSS feeds from various news sources"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SMSNewsBot/1.0)'
        })

    def fetch_feed(self, url: str, source_name: str) -> List[Dict]:
        """
        Fetch and parse a single RSS feed

        Args:
            url: RSS feed URL
            source_name: Name of the news source

        Returns:
            List of parsed articles
        """
        try:
            logger.info(f"Fetching feed from {source_name}: {url}")

            # Fetch the feed
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse with feedparser
            feed = feedparser.parse(response.content)

            articles = []
            for entry in feed.entries:
                article = self._parse_entry(entry, source_name)
                if article:
                    articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from {source_name}")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {source_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing feed from {source_name}: {e}")
            return []

    def _parse_entry(self, entry, source_name: str) -> Optional[Dict]:
        """Parse a single feed entry into article format"""
        try:
            # Extract publication date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = datetime.now()

            # Extract content/summary
            content = ""
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            elif hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value

            article = {
                "title": entry.get('title', 'No title'),
                "link": entry.get('link', ''),
                "published": published,
                "source": source_name,
                "content": content,
                "fetched_at": datetime.now()
            }

            return article

        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None

    def fetch_category(self, sources: List[Dict]) -> List[Dict]:
        """
        Fetch articles from multiple sources in a category

        Args:
            sources: List of source configurations

        Returns:
            Combined list of articles from all sources
        """
        all_articles = []

        for source in sources:
            articles = self.fetch_feed(source['url'], source['name'])
            # Add category info to each article
            for article in articles:
                article['category'] = source.get('category', 'general')
            all_articles.extend(articles)

        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x['published'], reverse=True)

        return all_articles

    def fetch_recent_articles(self, sources: List[Dict], hours: int = 24) -> List[Dict]:
        """
        Fetch only recent articles from the last N hours

        Args:
            sources: List of source configurations
            hours: Number of hours to look back

        Returns:
            List of recent articles
        """
        all_articles = self.fetch_category(sources)

        # Filter by time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_articles = [
            article for article in all_articles
            if article['published'] >= cutoff_time
        ]

        logger.info(f"Found {len(recent_articles)} articles from last {hours} hours")
        return recent_articles


# Convenience function
def fetch_news(category: str, hours: int = 24) -> List[Dict]:
    """
    Fetch news for a specific category

    Args:
        category: Category name (general, ai, tech, local)
        hours: Number of hours to look back

    Returns:
        List of articles
    """
    from .sources import get_sources_by_category

    sources = get_sources_by_category(category)
    if not sources:
        logger.warning(f"No sources found for category: {category}")
        return []

    fetcher = NewsFetcher()
    return fetcher.fetch_recent_articles(sources, hours=hours)
