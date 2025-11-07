"""
News source configurations for different categories
"""

NEWS_SOURCES = {
    "general": [
        {
            "name": "BBC World News",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
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
            "name": "AI News",
            "url": "https://www.artificialintelligence-news.com/feed/rss/",
            "type": "rss"
        },
        {
            "name": "Google DeepMind Blog",
            "url": "https://blog.google/technology/google-deepmind/rss/",
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
        }
    ],
    "local": [
        {
            "name": "BBC Turkish",
            "url": "https://feeds.bbci.co.uk/turkce/rss.xml",
            "type": "rss"
        }
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
