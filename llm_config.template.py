"""
LLM Configuration Template
Copy this file to llm_config.py and add your API key
"""
import os

# Get Gemini API key from environment variable or set directly
# Get your API key at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Uncomment and set your API key directly (not recommended for production)
# GEMINI_API_KEY = "your-api-key-here"

if not GEMINI_API_KEY:
    print("⚠️  Warning: GEMINI_API_KEY not configured")
    print("   Set it in this file or as environment variable")
    print("   Get one at: https://makersuite.google.com/app/apikey")
