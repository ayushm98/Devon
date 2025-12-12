import os
from dotenv import load_dotenv
import openai

load_dotenv()

# Get API key
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("❌ OPENAI_API_KEY not found in .env")
    exit(1)

print(f"✅ API key loaded: {api_key[:20]}...")

# Test connection
try:
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say 'API works!'"}],
        max_tokens=10
    )
    print(f"✅ API Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ API Error: {e}")
