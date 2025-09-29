"""Simple OpenAI client wrapper using httpx for async calls.

Environment variables:
- OPENAI_API_KEY (required)
- OPENAI_MODEL (optional, default gpt-4o-mini)
"""
import os
import httpx
from typing import Optional

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_TIMEOUT = float(os.getenv('OPENAI_TIMEOUT', '30'))


async def ask_openai(prompt: str, model: Optional[str] = None, temperature: float = 0.0) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY is not set')
    url = 'https://api.openai.com/v1/chat/completions'
    payload = {
        'model': model or OPENAI_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': float(temperature),
        'max_tokens': 800,
    }
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
    }
    async with httpx.AsyncClient(timeout=OPENAI_TIMEOUT) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        choice = data.get('choices', [{}])[0]
        if 'message' in choice:
            return choice['message'].get('content', '')
        return choice.get('text', '')
