"""Simple OpenAI client wrapper using httpx for async calls.

Environment variables:
- OPENAI_API_KEY (required)
- OPENAI_MODEL (optional, default gpt-4o-mini)
"""
import os
import httpx
from typing import Optional
from openai import OpenAI

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL')
OPENAI_TIMEOUT = float(os.getenv('OPENAI_TIMEOUT', '30'))
OPENAI_URL = os.getenv('OPENAI_URL')

def ask_openai(prompt: str, model: Optional[str] = None, temperature: float = 0.0) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY is not set')
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_URL, timeout=OPENAI_TIMEOUT)
    response = client.chat.completions.create(
        model=model or OPENAI_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return response.choices[0].message.content
