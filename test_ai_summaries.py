#!/usr/bin/env python3
"""
Test script for AI provider configuration
Tests both Claude and Gemini providers with sample articles
"""

import os
import sys
from dotenv import load_dotenv
from ai_summarizer import NewsSummarizer

# Load environment variables
load_dotenv()


def test_provider(provider_name: str):
    """Test a specific AI provider"""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name.upper()} Provider")
    print(f"{'='*60}\n")

    # Sample articles for testing
    sample_articles = [
        {
            "title": "OpenAI Announces GPT-5 with Advanced Reasoning",
            "source": "TechCrunch",
            "content": "OpenAI has unveiled GPT-5, featuring enhanced reasoning capabilities and multimodal understanding. The new model shows significant improvements in complex problem-solving tasks."
        },
        {
            "title": "Google DeepMind's AlphaFold 3 Predicts Protein Structures",
            "source": "Nature",
            "content": "Researchers at Google DeepMind have released AlphaFold 3, which can now predict protein-ligand interactions with unprecedented accuracy, opening new possibilities for drug discovery."
        },
        {
            "title": "Meta Releases Llama 4 Open Source Model",
            "source": "The Verge",
            "content": "Meta has open-sourced Llama 4, a new large language model that rivals proprietary alternatives. The model is available for commercial use under a permissive license."
        }
    ]

    try:
        # Initialize summarizer with specific provider
        summarizer = NewsSummarizer(provider=provider_name)

        # Generate summary
        print(f"Generating AI summary for {len(sample_articles)} articles...\n")
        summary = summarizer.summarize_articles(
            articles=sample_articles,
            category="ai",
            max_articles=5
        )

        print("✅ Summary generated successfully!\n")
        print("-" * 60)
        print(summary)
        print("-" * 60)
        print(f"\nSummary length: {len(summary)} characters")

        return True

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print(f"\nMake sure to set the required environment variables in your .env file:")
        if provider_name == 'claude':
            print("  - CLAUDE_API_KEY")
        elif provider_name == 'gemini':
            print("  - GEMINI_API_KEY")
        return False

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nInstall missing dependencies:")
        print("  pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run tests for configured providers"""
    print("\n" + "="*60)
    print("AI PROVIDER TEST SCRIPT")
    print("="*60)

    # Check which provider is configured
    configured_provider = os.getenv('AI_PROVIDER', 'claude').lower()
    print(f"\nConfigured AI Provider (from .env): {configured_provider}")

    # Test the configured provider
    success = test_provider(configured_provider)

    if not success:
        sys.exit(1)

    # Ask if user wants to test the other provider
    print("\n" + "="*60)
    other_provider = 'gemini' if configured_provider == 'claude' else 'claude'

    # Check if other provider has API key configured
    other_key_var = 'GEMINI_API_KEY' if other_provider == 'gemini' else 'CLAUDE_API_KEY'
    if os.getenv(other_key_var):
        print(f"\nDetected {other_provider.upper()} API key in environment.")
        print(f"Testing {other_provider} as well...\n")
        test_provider(other_provider)
    else:
        print(f"\nℹ️  {other_provider.upper()} not configured (no {other_key_var} found)")
        print(f"   To test {other_provider}, add {other_key_var} to your .env file")

    print("\n" + "="*60)
    print("✅ Testing complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
