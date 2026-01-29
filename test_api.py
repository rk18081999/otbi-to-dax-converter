import os
import google.generativeai as genai
from llm_config import GEMINI_API_KEY, GEMINI_MODEL

def test_api():
    print(f"Testing API with model: {GEMINI_MODEL}")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    try:
        response = model.generate_content("Hello, respond with 'API Working'")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
