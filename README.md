# SMS News Service - Daily Briefing Edition

An automated SMS-based news service that delivers AI-powered daily news briefings via text message. Perfect for staying informed on basic phones or when smartphone access is limited.

## Overview

This service runs as a scheduled daily job that:
1. Fetches news from RSS feeds across multiple categories (General, AI/Tech, Technology, Local)
2. Generates concise, AI-powered summaries using Claude or Gemini APIs
3. Sends daily briefings to subscribers via SMS (Twilio)
4. Implements retry logic with exponential backoff for reliable delivery

## Features

- 📰 **Multi-Category News**: General world news, AI/ML developments, tech industry, and local news
- 🤖 **AI-Powered Summaries**: Configurable AI providers (Claude or Gemini) for SMS-friendly briefings
- ⚡ **Single API Call**: All categories summarized in one AI request for efficiency
- 🎨 **Customizable Prompts**: Configure AI behavior via editable prompt template file
- 💰 **Cost-Effective**: Use Gemini's free tier (15 RPM, 1M TPM, 1500 RPD) for zero AI costs
- 📱 **SMS Delivery**: Reliable SMS delivery via Twilio with automatic retry
- ⏰ **Scheduled Delivery**: Runs daily at a specified time (default: 7 AM)
- 🔄 **Retry Logic**: Exponential backoff with up to 5 retry attempts per recipient
- 📊 **Comprehensive Logging**: Detailed logs for monitoring and debugging with prompt visibility

## Architecture

```
RSS Feeds → News Fetcher → AI API (Claude/Gemini) → Twilio SMS → Subscribers
```

### Components:

- **send_daily_news.py**: Main script that orchestrates the daily news service
- **news_aggregator/**: Fetches and parses RSS feeds
- **ai_summarizer.py**: Generates summaries using Claude or Gemini APIs (configurable)
- **prompt_config.txt**: Customizable AI prompt template
- **sms_service.py**: Handles SMS delivery with retry logic
- **subscribers.json**: List of subscriber phone numbers
- **logs/**: Execution logs

## Setup

### Prerequisites

- Python 3.8+
- Twilio account with SMS-enabled phone number
- AI API key (choose one):
  - **Gemini API** (recommended for personal use - free tier available)
  - **Claude API** (paid, higher quality)
- Server or computer that runs at scheduled time

### Installation

1. **Clone the repository**:
   ```bash
   cd sms_news
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

   Required variables:
   - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER`: Your Twilio phone number (E.164 format, e.g., +1234567890)
   - `AI_PROVIDER`: Choose `gemini` or `claude` (default: `claude`)
   - `GEMINI_API_KEY`: Your Google AI API key (if using Gemini - get from https://aistudio.google.com/apikey)
   - `CLAUDE_API_KEY`: Your Anthropic API key (if using Claude)

4. **Add subscribers**:
   Edit `subscribers.json` and add phone numbers in E.164 format:
   ```json
   {
     "subscribers": [
       "+11234567890",
       "+10987654321"
     ]
   }
   ```

5. **Test AI provider configuration**:
   ```bash
   python3 test_ai_summaries.py
   ```

   This will test your configured AI provider with sample articles.

6. **Test the full script**:
   ```bash
   # Test mode: no real SMS sent (recommended for first run)
   python3 send_daily_news.py --test

   # Production mode: send real SMS
   python3 send_daily_news.py
   ```

   This will:
   - Fetch latest news from RSS feeds
   - Generate AI summaries
   - Send to all subscribers (or simulate in test mode)
   - Log results to `logs/daily_news.log`

## Scheduling with Cron

### Option 1: System Cron (Recommended)

1. **Open crontab**:
   ```bash
   crontab -e
   ```

2. **Add cron job** (runs at 7 AM daily):
   ```bash
   0 7 * * * cd /path/to/sms_news && /usr/bin/python3 send_daily_news.py >> logs/cron.log 2>&1
   ```

   Replace `/path/to/sms_news` with your actual project path.

3. **Save and exit**

4. **Verify cron job**:
   ```bash
   crontab -l
   ```

### Cron Schedule Examples

```bash
# Daily at 7 AM
0 7 * * * cd /path/to/sms_news && python3 send_daily_news.py

# Daily at 8:30 AM
30 8 * * * cd /path/to/sms_news && python3 send_daily_news.py

# Weekdays only at 7 AM
0 7 * * 1-5 cd /path/to/sms_news && python3 send_daily_news.py

# Twice daily (7 AM and 6 PM)
0 7,18 * * * cd /path/to/sms_news && python3 send_daily_news.py
```

2. Add secrets in GitHub repository settings:
   - Settings → Secrets and variables → Actions → New repository secret
   - Add all required environment variables

**Note**: GitHub Actions scheduled workflows can be delayed by 3-10 minutes during high load times.

## Monitoring and Logs

### View Logs

```bash
# View latest logs
tail -f logs/daily_news.log

# View today's logs
grep "$(date +%Y-%m-%d)" logs/daily_news.log

# Check for errors
grep ERROR logs/daily_news.log
```

### Log Format

Logs include:
- Timestamp
- Logger name
- Log level
- Message

Example:
```
2025-01-26 07:00:01 - __main__ - INFO - Starting daily news service
2025-01-26 07:00:05 - news_aggregator.fetcher - INFO - Fetched 15 articles for general
2025-01-26 07:00:15 - ai_summarizer - INFO - Generated summary for general (842 chars)
2025-01-26 07:00:25 - sms_service - INFO - SMS sent successfully to +11234567890
```

## Customization

### Switch AI Providers

To switch between Claude and Gemini, simply update your `.env` file:
```bash
# Use Gemini (free tier)
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Or use Claude (paid)
AI_PROVIDER=claude
CLAUDE_API_KEY=your_claude_api_key_here
```
### Change News Sources

Edit `news_aggregator/sources.py` to add/remove RSS feeds:

```python
NEWS_SOURCES = {
    "general": [
        {
            "name": "Your News Source",
            "url": "https://example.com/rss",
            "type": "rss"
        }
    ]
}
```

### Customize AI Prompt

The AI summarization prompt is fully configurable via the `prompt_config.txt` file. The system now generates a **single comprehensive briefing** for all categories in one API call, making it more efficient and cost-effective.

**How it works:**
- All categories (general, AI, tech, local) are included in one prompt
- One AI API call generates the complete daily briefing
- Articles are organized by category in the prompt
- More cost-effective: 1 API call instead of 4

**Customization:**

**1. Edit the prompt file**:
   ```bash
   nano prompt_config.txt
   ```

**2. Customize the template** using these placeholders:
   - `{category_desc}`: Automatically filled with "multiple categories including world news, AI/ML, technology, and local news"
   - `{article_text}`: Automatically filled with all articles organized by category with headers

   Example article_text format:
   ```
   ### GENERAL (world news and current events) ###
   1. Article Title
      Source: BBC
      Preview: Content...

   ### AI (AI and machine learning developments) ###
   1. Article Title
      Source: OpenAI
      Preview: Content...
   ```

**3. Debug mode** - The full prompt is logged to console for debugging:
   ```bash
   python3 send_daily_news.py --test
   # You'll see the complete prompt printed before AI processing
   ```

**4. Environment variable override** (optional):
   ```bash
   # Use a different prompt file
   PROMPT_CONFIG_FILE=/path/to/custom_prompt.txt
   ```

**5. Programmatic override** (optional):
   ```python
   from ai_summarizer import NewsSummarizer
   summarizer = NewsSummarizer(prompt_file='custom_prompt.txt')
   ```

### Adjust Summary Length

Edit `ai_summarizer.py` and modify the max_tokens parameter:

```python
# Change max_tokens for longer/shorter summaries
message = self.client.messages.create(
    model=self.model,
    max_tokens=2048,  # Increase for longer summaries
    messages=[...]
)
```

### Change Delivery Time

Update your cron schedule (see Scheduling section above).

## Troubleshooting

### Script doesn't run
- Check cron logs: `grep CRON /var/log/syslog`
- Verify Python path: `which python3`
- Check file permissions: `ls -la send_daily_news.py`

### SMS not sending
- Verify Twilio credentials in `.env`
- Check Twilio account balance
- Verify phone numbers are in E.164 format (+1234567890)
- Check logs: `grep ERROR logs/daily_news.log`

### No news fetched
- Check internet connection
- Verify RSS feed URLs are accessible
- Check logs for specific feed errors

### API errors
- Verify Claude API key is valid
- Check API quota/limits
- Review error messages in logs

## Development

### Run Tests
```bash
# Test AI provider configuration
python3 test_ai_summaries.py

# Test news fetching
python3 -c "from news_aggregator.fetcher import fetch_news; print(fetch_news('general'))"

# Test AI summarization with specific provider
python3 -c "from ai_summarizer import NewsSummarizer; s = NewsSummarizer(provider='gemini'); print('Gemini configured')"
python3 -c "from ai_summarizer import NewsSummarizer; s = NewsSummarizer(provider='claude'); print('Claude configured')"

# Test full script WITHOUT sending real SMS (dry-run)
python3 send_daily_news.py --test

# Test full script with real SMS delivery
python3 send_daily_news.py
```

### Manual Execution
```bash
# Run the daily news script manually (test mode)
python3 send_daily_news.py --test

# Run in production mode (sends real SMS)
python3 send_daily_news.py

# Run with verbose logging
python3 send_daily_news.py --test 2>&1 | tee logs/manual_run.log
```

### Test Mode (--test flag)

The `--test` flag enables dry-run mode for safe testing:

**What it does:**
- ✅ Fetches real news from RSS feeds
- ✅ Generates real AI summaries
- ✅ Logs complete message content and recipients
- ❌ Does NOT send actual SMS messages via Twilio
- ❌ Does NOT consume SMS credits

**Usage:**
```bash
# Test the entire pipeline without sending SMS
python3 send_daily_news.py --test

# Check the logs to see what would have been sent
tail -f logs/daily_news.log
```

**When to use test mode:**
- First-time setup and testing
- Testing configuration changes
- Verifying news sources and AI summaries
- Debugging without SMS costs
- Checking message formatting and length

---

