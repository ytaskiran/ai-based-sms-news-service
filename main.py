from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
import uvicorn
import os
from dotenv import load_dotenv
from datetime import datetime
from contextlib import asynccontextmanager

from news_aggregator.scheduler import start_scheduler, get_scheduler
from database.models import get_db

load_dotenv()

# In-memory cache for tracking usage (will be replaced with Redis/DB later)
usage_tracker = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - start/stop background tasks"""
    # Startup
    scheduler = start_scheduler()
    # Optionally fetch news immediately on startup
    await scheduler.fetch_all_categories()
    yield
    # Shutdown
    scheduler.stop()


app = FastAPI(title="SMS News Service", lifespan=lifespan)

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "sms-news"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook/sms")
async def handle_incoming_sms(Body: str = Form(...), From: str = Form(...)):
    """Handle incoming SMS messages and route commands"""
    response = MessagingResponse()

    command = Body.upper().strip()
    phone_number = From

    # Log the incoming message
    print(f"[{datetime.now()}] SMS from {phone_number}: {command}")

    # Track basic usage (will implement rate limiting later)
    if phone_number not in usage_tracker:
        usage_tracker[phone_number] = []
    usage_tracker[phone_number].append(datetime.now())

    # Command routing
    if command == "NEWS" or command == "GENERAL":
        message = generate_general_news()
    elif command == "AI":
        message = generate_ai_news()
    elif command == "TECH":
        message = generate_tech_news()
    elif command == "LOCAL":
        message = generate_local_news()
    elif command == "YESTERDAY":
        message = generate_yesterday_summary()
    elif command == "HELP":
        message = get_help_text()
    else:
        message = f"Unknown command: '{Body}'\n\nText HELP for available commands."

    response.message(message)
    return Response(content=str(response), media_type="application/xml")


def generate_general_news():
    """Generate general news summary"""
    db = get_db()
    articles = db.get_articles('general', limit=10)

    if not articles:
        return "📰 GENERAL NEWS\n\nNo recent articles available. Try again in a few minutes!"

    # Format articles for SMS (AI summarization will be added in Phase 3)
    message = "📰 GENERAL NEWS\n\n"
    for i, article in enumerate(articles[:5], 1):
        title = article.get('title', 'No title')[:100]
        source = article.get('source', 'Unknown')
        message += f"{i}. {title}\n   ({source})\n\n"

    message += "Full summaries coming soon with AI integration!"
    return message


def generate_ai_news():
    """Generate AI/tech news summary"""
    db = get_db()
    articles = db.get_articles('ai', limit=10)

    if not articles:
        return "🤖 AI NEWS\n\nNo recent articles available. Try again in a few minutes!"

    message = "🤖 AI NEWS\n\n"
    for i, article in enumerate(articles[:5], 1):
        title = article.get('title', 'No title')[:100]
        source = article.get('source', 'Unknown')
        message += f"{i}. {title}\n   ({source})\n\n"

    message += "Full summaries coming soon with AI integration!"
    return message


def generate_tech_news():
    """Generate tech industry news"""
    db = get_db()
    articles = db.get_articles('tech', limit=10)

    if not articles:
        return "💻 TECH NEWS\n\nNo recent articles available. Try again in a few minutes!"

    message = "💻 TECH NEWS\n\n"
    for i, article in enumerate(articles[:5], 1):
        title = article.get('title', 'No title')[:100]
        source = article.get('source', 'Unknown')
        message += f"{i}. {title}\n   ({source})\n\n"

    message += "Full summaries coming soon with AI integration!"
    return message


def generate_local_news():
    """Generate local news summary (placeholder)"""
    return (
        "📍 LOCAL NEWS (Coming Soon)\n\n"
        "This feature will provide news from your local area.\n\n"
        "Currently in development!"
    )


def generate_yesterday_summary():
    """Generate yesterday's summary (placeholder)"""
    return (
        "📅 YESTERDAY'S SUMMARY (Coming Soon)\n\n"
        "This feature will provide a recap of yesterday's top stories across all categories.\n\n"
        "Currently in development!"
    )


def get_help_text():
    """Return help text with available commands"""
    return (
        "📱 SMS NEWS SERVICE - COMMANDS\n\n"
        "NEWS - General news summary\n"
        "AI - AI & ML developments\n"
        "TECH - Tech industry news\n"
        "LOCAL - Local news\n"
        "YESTERDAY - Yesterday's recap\n"
        "HELP - Show this message\n\n"
        "Text any command to get started!"
    )


@app.get("/stats")
async def get_stats():
    """Internal endpoint to view usage statistics"""
    db = get_db()
    total_requests = sum(len(requests) for requests in usage_tracker.values())

    # Get article counts per category
    article_counts = {
        'general': len(db.get_articles('general', limit=1000)),
        'ai': len(db.get_articles('ai', limit=1000)),
        'tech': len(db.get_articles('tech', limit=1000))
    }

    return {
        "total_users": len(usage_tracker),
        "total_requests": total_requests,
        "users": {phone: len(requests) for phone, requests in usage_tracker.items()},
        "articles_stored": article_counts,
        "total_articles": sum(article_counts.values())
    }


@app.post("/admin/fetch-news")
async def manual_fetch_news(category: str = None):
    """Manual endpoint to trigger news fetch"""
    scheduler = get_scheduler()
    await scheduler.fetch_now(category)
    return {"status": "success", "message": f"Fetched news for {category or 'all categories'}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
