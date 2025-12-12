import os
from dotenv import load_dotenv

load_dotenv()

openai_key = os.getenv('OPENAI_API_KEY')
e2b_key = os.getenv('E2B_API_KEY')

if openai_key:
      print(f"✅ OpenAI key loaded: {openai_key[:15]}...")
else:
      print("❌ OpenAI key missing")

if e2b_key:
      print(f"✅ E2B key loaded: {e2b_key[:15]}...")
else:
      print("❌ E2B key missing")

print("\n✅ All packages imported successfully!")