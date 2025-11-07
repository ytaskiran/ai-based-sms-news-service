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
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install it with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)

        # Configure safety settings for news content (less restrictive)
        # News may contain sensitive topics that shouldn't be blocked
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        self.model = genai.GenerativeModel(model)
        self.genai = genai  # Keep reference for FinishReason enum

    def summarize(self, prompt: str, max_tokens: int = 1024) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
            },
            safety_settings=self.safety_settings
        )

        # Check if response was blocked at prompt level
        if not response.candidates:
            raise ValueError(
                f"Gemini blocked the response. Prompt feedback: {response.prompt_feedback}"
            )

        candidate = response.candidates[0]

        # Check finish reason
        # FinishReason values: FINISH_REASON_UNSPECIFIED=0, STOP=1, MAX_TOKENS=2, SAFETY=3, RECITATION=4, OTHER=5
        # Use numeric comparison for compatibility across SDK versions
        finish_reason_value = int(candidate.finish_reason)

        # Check if we have valid parts/content before accessing text
        # The SDK throws an error when accessing response.text if no valid parts exist
        has_valid_parts = (
            hasattr(candidate, 'content') and
            hasattr(candidate.content, 'parts') and
            len(candidate.content.parts) > 0
        )

        if not has_valid_parts:
            finish_reason_name = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)

            # Get safety ratings if available
            safety_info = ""
            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                safety_info = f"\nSafety ratings: {candidate.safety_ratings}"

            error_msg = f"Gemini returned no content. Finish reason: {finish_reason_name} (value: {finish_reason_value}){safety_info}\n"

            if finish_reason_value == 2:  # MAX_TOKENS - hit output limit
                error_msg += "Hit the output token limit before generating valid content. This is unusual.\n"
                error_msg += "Possible causes:\n"
                error_msg += "1. Output token limit is too low (try increasing max_tokens)\n"
                error_msg += "2. Model started generating but was blocked mid-stream\n"
                error_msg += "3. Safety filters triggered during generation\n"
                error_msg += "Note: This was just fixed - token limit increased from 2048 to 4096. Try again."
            elif finish_reason_value == 3:  # SAFETY
                error_msg += "Content was blocked by safety filters. Try adjusting news sources or use Claude provider."
            elif finish_reason_value == 4:  # RECITATION
                error_msg += "Content was blocked due to recitation (too similar to training data)."
            else:
                error_msg += "Generation stopped unexpectedly."

            raise ValueError(error_msg)

        # 1 = STOP (normal completion), 2 = MAX_TOKENS (also acceptable for valid content)
        if finish_reason_value not in [1, 2]:
            finish_reason_name = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
            safety_info = ""
            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                safety_info = f"\nSafety ratings: {candidate.safety_ratings}"

            raise ValueError(
                f"Gemini stopped with finish_reason: {finish_reason_name} (value: {finish_reason_value}){safety_info}"
            )

        # Now safe to access response.text
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
        return """You are a news summarization assistant. Create a concise, SMS-friendly daily news briefing covering {category_desc}.

Here are today's top articles organized by category:
{article_text}

Generate a comprehensive daily briefing that:
1. Covers ALL categories provided (general news, AI/ML, technology, local news)
2. Highlights the most important stories from each category (2-4 stories per category)
3. Is optimized for SMS delivery (concise but informative)
4. Uses clear, accessible language
5. Organizes content with clear category headers and separators
6. Does NOT use emojis or special formatting
7. Keeps total length reasonable for SMS (1500-2500 characters total)

Format example:
WORLD NEWS
----------
[2-3 key stories with brief summaries]

AI & MACHINE LEARNING
---------------------
[2-3 key AI/ML developments]

TECHNOLOGY
----------
[2-3 key tech stories]

LOCAL NEWS
----------
[2-3 key local updates]"""

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

            # Log prompt
            logger.debug(f"Prompt for {category}:")
            logger.debug(prompt)

            # Call AI provider
            summary = self.provider.summarize(prompt, max_tokens=1024)

            logger.info(f"Generated summary for {category} ({len(summary)} chars)")

            # Log response
            logger.debug(f"Response for {category}:")
            logger.debug(summary)

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
        articles_by_category: Dict[str, List[Dict]],
        max_articles_per_category: int = 10
    ) -> str:
        """
        Generate comprehensive daily briefing with all categories in a single AI call

        Args:
            articles_by_category: Dict mapping category names to article lists
            max_articles_per_category: Maximum number of articles per category

        Returns:
            Complete daily briefing text
        """
        # Filter out empty categories and limit articles
        filtered_categories = {}
        for category, articles in articles_by_category.items():
            if articles:
                filtered_categories[category] = articles[:max_articles_per_category]

        if not filtered_categories:
            logger.warning("No articles available for any category")
            return "No news available at this time."

        # Build single prompt with all categories
        prompt = self._build_multi_category_prompt(filtered_categories)

        try:
            logger.info(f"Generating daily briefing for {len(filtered_categories)} categories using {self.provider_name}")
            logger.info(f"Total articles: {sum(len(articles) for articles in filtered_categories.values())}")

            # Log the full prompt for debugging
            logger.debug("=" * 80)
            logger.debug("PROMPT TO AI MODEL:")
            logger.debug("=" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)

            # Also print to console for immediate visibility
            print("\n" + "=" * 80)
            print("PROMPT TO AI MODEL:")
            print("=" * 80)
            print(prompt)
            print("=" * 80 + "\n")

            # Single AI call for all categories
            briefing = self.provider.summarize(prompt, max_tokens=10000)

            logger.info(f"Generated complete briefing ({len(briefing)} chars)")

            # Log the AI response
            logger.debug("=" * 80)
            logger.debug("RESPONSE FROM AI MODEL:")
            logger.debug("=" * 80)
            logger.debug(briefing)
            logger.debug("=" * 80)

            # Also print to console for immediate visibility
            print("\n" + "=" * 80)
            print("RESPONSE FROM AI MODEL:")
            print("=" * 80)
            print(briefing)
            print("=" * 80 + "\n")

            return briefing

        except Exception as e:
            logger.error(f"Error generating daily briefing with {self.provider_name}: {e}")
            return self._fallback_multi_category_summary(filtered_categories)

    def _build_multi_category_prompt(self, articles_by_category: Dict[str, List[Dict]]) -> str:
        """
        Build prompt for all categories at once using template from file

        Args:
            articles_by_category: Dict mapping category names to article lists

        Returns:
            Formatted prompt string
        """
        # Category descriptions
        category_instructions = {
            "general": "world news and current events",
            "ai": "AI and machine learning developments",
            "tech": "technology industry news and innovations",
            "local": "local news and community updates"
        }

        # Build organized article text with category sections
        article_text = ""
        for category, articles in articles_by_category.items():
            category_desc = category_instructions.get(category, category)
            article_text += f"\n### {category.upper()} ({category_desc}) ###\n"

            for i, article in enumerate(articles, 1):
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                content = article.get('content', '')[:500]

                article_text += f"\n{i}. {title}\n"
                article_text += f"   Source: {source}\n"
                if content:
                    article_text += f"   Preview: {content}\n"

            article_text += "\n"

        # Use template from file with all categories
        prompt = self.prompt_template.format(
            category_desc="multiple categories including world news, AI/ML, technology, and local news",
            article_text=article_text
        )

        return prompt

    def _fallback_multi_category_summary(self, articles_by_category: Dict[str, List[Dict]]) -> str:
        """
        Generate simple fallback summary for all categories if AI fails

        Args:
            articles_by_category: Dict mapping category names to article lists

        Returns:
            Basic text summary
        """
        category_labels = {
            "general": "GENERAL NEWS",
            "ai": "AI NEWS",
            "tech": "TECH NEWS",
            "local": "LOCAL NEWS"
        }

        summary = "DAILY NEWS BRIEFING\n\n"

        for category, articles in articles_by_category.items():
            label = category_labels.get(category, category.upper())
            summary += f"{label}\n{'-' * len(label)}\n"

            for i, article in enumerate(articles[:5], 1):
                title = article.get('title', 'No title')[:100]
                source = article.get('source', 'Unknown')
                summary += f"{i}. {title}\n   ({source})\n\n"

            summary += "\n"

        summary += "AI summary temporarily unavailable."

        return summary
