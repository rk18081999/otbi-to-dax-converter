import requests
import json
from llm_config import GEMINI_API_KEY, GEMINI_MODEL

def test_request():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts":[{"text": "Hello, respond with 'API Working'"}]
        }]
    }
    
    print(f"Sending request to {GEMINI_MODEL}...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()['candidates'][0]['content']['parts'][0]['text']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_request()
