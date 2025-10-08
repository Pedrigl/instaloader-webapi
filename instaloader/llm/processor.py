"""LLM processor shim to extract supermarket item entities from story/post media.

This is a small abstraction so you can later plug any LLM provider (OpenAI, local
Llama, Cohere, etc.). For now it contains a naive heuristic parser that can be
used for testing, and a placeholder async function `describe_image_with_llm`
that should be replaced with a real LLM call.
"""
from typing import List, Dict, Any
import base64
import json
import os
from .openai_client import ask_openai


LLM_PRODUCT_PROMPT = """
You will be given a textual description of an image or a base64 image prefix.
Extract supermarket products depicted in the image and return a JSON array of
objects matching this interface:

[
  {
    "id": "<unique id   >",
    "title": "<product title>",
    "marketPrices": [{"market":"<name of supermarket market>", "price": <number>}],
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

    # debug toggle
    DEBUG = os.getenv("LLM_DEBUG", "").lower() in ("1", "true", "yes")

    try:
        resp = ask_openai(prompt, temperature=0.0)
    except Exception as e:
        # surface exact LLM client error (API key missing, network, import error, etc)
        print(f"LLM call failed: {type(e).__name__}: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        return []

    # try parse JSON but log the response preview on failure
    try:
        parsed = json.loads(resp)
    except Exception as e:
        preview = (resp[:2000] + "...") if isinstance(resp, str) else str(resp)
        print("LLM response was not valid JSON:", type(e).__name__, e)
        print("LLM response preview:", preview)
        return []

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

    # unexpected shape
    if DEBUG:
        print("LLM returned non-list JSON:", parsed)
    return []
