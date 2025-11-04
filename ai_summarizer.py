"""
AI-powered news summarization using Claude or Gemini APIs
Optimized for SMS delivery with concise, informative summaries
"""

import os
import logging
from typing import List, Dict, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AIProvider:
    """Base class for AI providers"""

    def summarize(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate summary from prompt"""
        raise NotImplementedError


class ClaudeProvider(AIProvider):
    """Claude API provider"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def summarize(self, prompt: str, max_tokens: int = 1024) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()


class GeminiProvider(AIProvider):
    """Google Gemini API provider"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install it with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def summarize(self, prompt: str, max_tokens: int = 1024) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
            }
        )
        return response.text.strip()


class NewsSummarizer:
    """Generate SMS-friendly news summaries using configurable AI providers"""

    def __init__(
        self,
        provider: str = None,
        api_key: str = None,
        model: str = None,
        prompt_file: str = None
    ):
        """
        Initialize AI summarizer with configurable provider

        Args:
            provider: AI provider ('claude' or 'gemini', defaults to env AI_PROVIDER or 'claude')
            api_key: API key (defaults to provider-specific env var)
            model: Model name (defaults to provider-specific default)
            prompt_file: Path to prompt template file (defaults to 'prompt_config.txt')
        """
        # Determine provider
        self.provider_name = provider or os.getenv('AI_PROVIDER', 'claude').lower()

        if self.provider_name not in ['claude', 'gemini']:
            raise ValueError(f"Unsupported AI provider: {self.provider_name}. Use 'claude' or 'gemini'")

        # Initialize provider-specific client
        if self.provider_name == 'claude':
            api_key = api_key or os.getenv('CLAUDE_API_KEY')
            if not api_key:
                raise ValueError("Missing Claude API key. Set CLAUDE_API_KEY environment variable")

            model = model or os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
            self.provider = ClaudeProvider(api_key, model)

        elif self.provider_name == 'gemini':
            api_key = api_key or os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Missing Gemini API key. Set GEMINI_API_KEY environment variable")

            model = model or os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
            self.provider = GeminiProvider(api_key, model)

        # Load prompt template
        self.prompt_file = prompt_file or os.getenv('PROMPT_CONFIG_FILE', 'prompt_config.txt')
        self.prompt_template = self._load_prompt_template()

        logger.info(f"Initialized NewsSummarizer with provider: {self.provider_name}")

    def _load_prompt_template(self) -> str:
        """
        Load prompt template from file

        Returns:
            Prompt template string
        """
        try:
            # Try relative to script directory first
            if not os.path.isabs(self.prompt_file):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                prompt_path = os.path.join(script_dir, self.prompt_file)
            else:
                prompt_path = self.prompt_file

            with open(prompt_path, 'r', encoding='utf-8') as f:
                template = f.read().strip()
                logger.info(f"Loaded prompt template from {prompt_path}")
                return template

        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {self.prompt_file}. Using default prompt.")
            return self._get_default_prompt()
        except Exception as e:
            logger.error(f"Error loading prompt file: {e}. Using default prompt.")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """
        Get default prompt template if file loading fails

        Returns:
            Default prompt template string
        """
        return """You are a news summarization assistant. Create a concise, SMS-friendly daily news briefing for {category_desc}.

Here are today's top articles:
{article_text}

Generate a brief, informative summary that:
1. Highlights the most important stories (3-5 key stories)
2. Is optimized for SMS delivery (concise but informative)
3. Uses clear, accessible language
4. Can be 500-1200 characters (aim for readability on a phone screen)
5. Includes a brief headline or key point for each major story
6. Does NOT use emojis or special formatting
7. Separates stories with clear line breaks

Format as a clean text summary suitable for SMS delivery."""

    def summarize_articles(
        self,
        articles: List[Dict],
        category: str,
        max_articles: int = 10
    ) -> str:
        """
        Generate SMS-optimized summary of news articles

        Args:
            articles: List of article dictionaries
            category: Category name (general, ai, tech, local)
            max_articles: Maximum number of articles to summarize

        Returns:
            SMS-friendly summary text
        """
        if not articles:
            return self._empty_message(category)

        # Limit number of articles
        articles = articles[:max_articles]

        # Build prompt with article data
        prompt = self._build_prompt(articles, category)

        try:
            logger.info(f"Generating summary for {len(articles)} {category} articles using {self.provider_name}")

            # Call AI provider
            summary = self.provider.summarize(prompt, max_tokens=1024)

            logger.info(f"Generated summary for {category} ({len(summary)} chars)")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary with {self.provider_name}: {e}")
            return self._fallback_summary(articles, category)

    def _build_prompt(self, articles: List[Dict], category: str) -> str:
        """
        Build prompt with article data using template from file

        Args:
            articles: List of articles
            category: Category name

        Returns:
            Formatted prompt string
        """
        # Category-specific instructions
        category_instructions = {
            "general": "world news and current events",
            "ai": "AI and machine learning developments",
            "tech": "technology industry news and innovations",
            "local": "local news and community updates"
        }

        category_desc = category_instructions.get(category, "news")

        # Build article list
        article_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown')
            content = article.get('content', '')[:500]  # Limit content length

            article_text += f"\n{i}. {title}\n"
            article_text += f"   Source: {source}\n"
            if content:
                article_text += f"   Preview: {content}\n"

        # Use template from file with variable substitution
        prompt = self.prompt_template.format(
            category_desc=category_desc,
            article_text=article_text
        )

        return prompt

    def _fallback_summary(self, articles: List[Dict], category: str) -> str:
        """
        Generate simple fallback summary if API fails

        Args:
            articles: List of articles
            category: Category name

        Returns:
            Basic text summary
        """
        category_labels = {
            "general": "GENERAL NEWS",
            "ai": "AI NEWS",
            "tech": "TECH NEWS",
            "local": "LOCAL NEWS"
        }

        label = category_labels.get(category, "NEWS")
        summary = f"{label} - {len(articles)} stories\n\n"

        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', 'No title')[:100]
            source = article.get('source', 'Unknown')
            summary += f"{i}. {title}\n   ({source})\n\n"

        summary += "AI summary temporarily unavailable."

        return summary

    def _empty_message(self, category: str) -> str:
        """
        Generate message when no articles are available

        Args:
            category: Category name

        Returns:
            Empty state message
        """
        category_labels = {
            "general": "GENERAL NEWS",
            "ai": "AI NEWS",
            "tech": "TECH NEWS",
            "local": "LOCAL NEWS"
        }

        label = category_labels.get(category, "NEWS")

        return f"{label}\n\nNo recent articles available at this time. Please check back later!"

    def generate_daily_briefing(
        self,
        articles_by_category: Dict[str, List[Dict]]
    ) -> str:
        """
        Generate comprehensive daily briefing with all categories

        Args:
            articles_by_category: Dict mapping category names to article lists

        Returns:
            Complete daily briefing text
        """
        briefing = "DAILY NEWS BRIEFING\n"
        briefing += "=" * 30 + "\n\n"

        categories = ["general", "ai", "tech", "local"]

        for category in categories:
            articles = articles_by_category.get(category, [])

            if not articles:
                continue

            # Generate summary for this category
            summary = self.summarize_articles(articles, category)

            briefing += f"\n{summary}\n"
            briefing += "\n" + "-" * 30 + "\n"

        briefing += "\n\nStay informed!"

        return briefing
