"""
LLM Configuration Template
Copy this file to llm_config.py and add your API key
"""
import os

# Get Gemini API key from environment variable or set directly
# Get your API key at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"  # or gemini-2.5-pro for higher quality reasoning

# Uncomment and set your API key directly (not recommended for production)
GEMINI_API_KEY = "AIzaSyCu8zTV0MJTX06DwaUDy8Tz8WO2Fk8lRxU"

if not GEMINI_API_KEY:
    print("⚠️  Warning: GEMINI_API_KEY not configured")
    print("   Set it in this file or as environment variable")
    print("   Get one at: https://makersuite.google.com/app/apikey")
