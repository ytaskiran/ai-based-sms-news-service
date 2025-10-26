"""
News source configurations for different categories
"""

NEWS_SOURCES = {
    "general": [
        {
            "name": "BBC World News",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "type": "rss"
        },
        {
            "name": "Reuters World News",
            "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            "type": "rss"
        },
        {
            "name": "AP News",
            "url": "https://rsshub.app/apnews/topics/apf-topnews",
            "type": "rss"
        }
    ],
    "ai": [
        {
            "name": "OpenAI Blog",
            "url": "https://openai.com/blog/rss.xml",
            "type": "rss"
        },
        {
            "name": "Anthropic News",
            "url": "https://www.anthropic.com/news/rss.xml",
            "type": "rss"
        },
        {
            "name": "Machine Learning Subreddit",
            "url": "https://www.reddit.com/r/MachineLearning/top/.rss?t=day",
            "type": "rss"
        },
        {
            "name": "AI News",
            "url": "https://www.artificialintelligence-news.com/feed/",
            "type": "rss"
        }
    ],
    "tech": [
        {
            "name": "Hacker News",
            "url": "https://hnrss.org/frontpage",
            "type": "rss"
        },
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
            "type": "rss"
        },
        {
            "name": "The Verge",
            "url": "https://www.theverge.com/rss/index.xml",
            "type": "rss"
        },
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/index",
            "type": "rss"
        }
    ],
    "local": [
        # Will be configured based on user location
        # Placeholder for now
    ]
}


def get_sources_by_category(category: str):
    """Get news sources for a specific category"""
    return NEWS_SOURCES.get(category, [])


def get_all_sources():
    """Get all news sources across all categories"""
    all_sources = []
    for category, sources in NEWS_SOURCES.items():
        for source in sources:
            source_copy = source.copy()
            source_copy["category"] = category
            all_sources.append(source_copy)
    return all_sources
