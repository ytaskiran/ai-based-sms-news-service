"""
Quick test script to verify Phase 2 integration
"""
import asyncio
from news_aggregator.scheduler import get_scheduler
from database.models import get_db


async def test_phase_2():
    """Test news aggregation and database storage"""
    print("=" * 60)
    print("PHASE 2 TEST - News Aggregation")
    print("=" * 60)

    # Initialize
    scheduler = get_scheduler()
    db = get_db()

    # Fetch news for all categories
    print("\n1. Fetching news for all categories...")
    await scheduler.fetch_all_categories()

    # Check what was stored
    print("\n2. Checking database:")
    for category in ['general', 'ai', 'tech']:
        articles = db.get_articles(category, limit=5)
        print(f"\n   {category.upper()}: {len(articles)} articles")
        for i, article in enumerate(articles[:3], 1):
            print(f"      {i}. {article['title'][:60]}...")
            print(f"         Source: {article['source']}")

    print("\n" + "=" * 60)
    print("Phase 2 test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_phase_2())
