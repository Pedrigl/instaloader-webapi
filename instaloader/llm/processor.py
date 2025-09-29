"""LLM processor shim to extract supermarket item entities from story/post media.

This is a small abstraction so you can later plug any LLM provider (OpenAI, local
Llama, Cohere, etc.). For now it contains a naive heuristic parser that can be
used for testing, and a placeholder async function `describe_image_with_llm`
that should be replaced with a real LLM call.
"""
from typing import List, Dict, Any
import base64
import json

from .openai_client import ask_openai


LLM_PRODUCT_PROMPT = """
You will be given a textual description of an image or a base64 image prefix.
Extract supermarket products depicted in the image and return a JSON array of
objects matching this interface:

[
  {
    "id": "<unique id>",
    "title": "<product title>",
    "marketPrices": [{"market":"<market>", "price": <number>}],
    "imageUrl": "<optional image url>",
    "description": "<short description>"
  }
]

Return ONLY valid JSON (a single JSON array). If none, return []
"""


async def extract_items_from_image(image_bytes: bytes, source_type: str, source_id: str) -> List[Dict[str, Any]]:
    # create truncated base64 to avoid huge payloads
    b64 = base64.b64encode(image_bytes).decode('ascii')
    truncated = b64[:12000]
    prompt = LLM_PRODUCT_PROMPT + "\n\nBase64ImagePrefix: " + truncated
    try:
        resp = await ask_openai(prompt, temperature=0.0)
        parsed = json.loads(resp)
        if isinstance(parsed, list):
            normalized = []
            for item in parsed:
                normalized.append({
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'marketPrices': item.get('marketPrices') or [],
                    'imageUrl': item.get('imageUrl') or item.get('image_url') or '',
                    'description': item.get('description') or '',
                    'source_type': source_type,
                    'source_id': source_id,
                    'raw_data': item,
                })
            return normalized
    except Exception:
        # fallback to empty list
        return []
    return []
