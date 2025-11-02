#!/usr/bin/env python3
"""
Test script for daily news service
Tests news fetching and summarization without sending SMS
"""

import os
import sys
from dotenv import load_dotenv
from news_aggregator.fetcher import NewsFetcher
from news_aggregator.sources import get_sources_by_category
from ai_summarizer import NewsSummarizer

load_dotenv()

def test_news_fetching():
    """Test fetching news from RSS feeds"""
    print("=" * 60)
    print("Testing News Fetching")
    print("=" * 60)

    fetcher = NewsFetcher()
    categories = ["general", "ai", "tech"]

    for category in categories:
        print(f"\n{category.upper()} NEWS:")
        print("-" * 40)

        sources = get_sources_by_category(category)
        print(f"Sources configured: {len(sources)}")

        articles = fetcher.fetch_recent_articles(sources, hours=24)
        print(f"Articles fetched: {len(articles)}")

        if articles:
            print(f"\nFirst article:")
            print(f"  Title: {articles[0].get('title', 'N/A')[:80]}")
            print(f"  Source: {articles[0].get('source', 'N/A')}")
            print(f"  Published: {articles[0].get('published', 'N/A')}")

    print("\n✓ News fetching test complete!")
    return True

def test_ai_summarization():
    """Test AI summarization (requires Claude API key)"""
    print("\n" + "=" * 60)
    print("Testing AI Summarization")
    print("=" * 60)

    api_key = os.getenv('CLAUDE_API_KEY')

    if not api_key or api_key == 'your_claude_api_key_here':
        print("⚠ Claude API key not configured - skipping AI test")
        print("Set CLAUDE_API_KEY in .env to test AI summarization")
        return False

    try:
        summarizer = NewsSummarizer()
        print("✓ Claude API client initialized")

        # Create test articles
        test_articles = [
            {
                "title": "Test Article 1: Major Tech Announcement",
                "source": "Test Source",
                "content": "This is a test article about a major technology announcement.",
                "published": "2025-01-26"
            },
            {
                "title": "Test Article 2: AI Breakthrough",
                "source": "Test Source",
                "content": "Researchers announce breakthrough in artificial intelligence.",
                "published": "2025-01-26"
            }
        ]

        print("\nGenerating test summary...")
        summary = summarizer.summarize_articles(test_articles, "tech")

        print("\nGenerated Summary:")
        print("-" * 40)
        print(summary)
        print("-" * 40)
        print(f"\nSummary length: {len(summary)} characters")

        print("\n✓ AI summarization test complete!")
        return True

    except Exception as e:
        print(f"✗ AI summarization test failed: {e}")
        return False

def test_configuration():
    """Test that all required configuration is present"""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    required_vars = {
        'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
        'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
        'TWILIO_PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER'),
        'CLAUDE_API_KEY': os.getenv('CLAUDE_API_KEY'),
    }

    all_configured = True

    for var, value in required_vars.items():
        if not value or 'your_' in value:
            print(f"✗ {var}: Not configured")
            all_configured = False
        else:
            # Mask sensitive values
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var}: {masked}")

    if all_configured:
        print("\n✓ All configuration variables set!")
    else:
        print("\n⚠ Some configuration variables missing")
        print("Update .env with your API keys to enable full functionality")

    return all_configured

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DAILY NEWS SERVICE - TEST SUITE")
    print("=" * 60)

    results = {
        "Configuration": test_configuration(),
        "News Fetching": test_news_fetching(),
        "AI Summarization": test_ai_summarization(),
    }

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    for test, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED/SKIPPED"
        print(f"{test}: {status}")

    print("\n" + "=" * 60)

    if all(results.values()):
        print("✓ All tests passed! Ready to send daily news.")
        print("\nNext steps:")
        print("1. Add phone numbers to subscribers.json")
        print("2. Run: python3 send_daily_news.py")
        print("3. Set up cron job for daily execution")
    else:
        print("⚠ Some tests failed or were skipped.")
        print("Configure missing environment variables in .env")

    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
