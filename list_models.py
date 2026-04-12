import os
from google import genai
from dotenv import load_dotenv

load_dotenv(r'd:\AI CLG Project\.env')
api_key = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=api_key)
for m in client.models.list():
    print(m.name)
