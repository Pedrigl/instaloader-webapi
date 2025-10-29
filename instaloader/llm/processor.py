"""LLM processor shim to extract supermarket item entities from story/post media.

This is a small abstraction so you can later plug any LLM provider (OpenAI, local
Llama, Cohere, etc.). For now it contains a naive heuristic parser that can be
used for testing, and a placeholder async function `describe_image_with_llm`
that should be replaced with a real LLM call.
"""
from typing import List, Dict, Any, Optional
import base64
import json
import os
import re
import asyncio
from .openai_client import ask_openai

try:
    from PIL import Image
    import pytesseract
    _HAS_OCR = True
except Exception:
    _HAS_OCR = False


LLM_PRODUCT_PROMPT = """
System: You are an extractor that returns a JSON array of supermarket product objects.
Always reply with a single valid JSON array and nothing else (no prose, no code fences).

Example:
Input image/text -> Output (example)
    [image of a Coke can]
    => [{"id":"coke-can-330ml","title":"Coca-Cola 330ml Can","marketPrices":[{"market":"Gigante Atacadista","price":5.99}],"imageUrl":null,"description":"Red can, Coca-Cola logo."}]

Now extract products from the following story metadata + image prefix.

"""
def _strip_code_fences(s: str) -> str:
    s = (s or "").strip()
    # Remove surrounding Markdown code fences like ```json ... ```
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s, flags=re.IGNORECASE)
    return s.strip()


def _extract_json_array_text(s: str) -> Optional[str]:
    if not s:
        return None
    start = s.find("[")
    end = s.rfind("]")
    if start != -1 and end != -1 and end > start:
        return s[start:end + 1]
    return None


async def extract_items_from_image(
    image_bytes: bytes,
    source_type: str,
    *,
    image_url: Optional[str] = None,
    username: Optional[str] = None,
    date: Optional[str] = None,
    shortcode: Optional[str] = None,
    market_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Call the LLM with image prefix + story metadata and return normalized products."""
    # create truncated base64 to avoid huge payloads
    b64 = base64.b64encode(image_bytes).decode('ascii')
    truncated = b64[:12000]

    # optional OCR to include text context (if available)
    ocr_text = None
    if _HAS_OCR:
        try:
            from io import BytesIO

            img = Image.open(BytesIO(image_bytes))
            ocr_text = pytesseract.image_to_string(img).strip()
            if not ocr_text:
                ocr_text = None
        except Exception:
            ocr_text = None

    prompt = LLM_PRODUCT_PROMPT + "\nStory metadata:\n"
    meta = {
        "username": username,
        "shortcode": shortcode,
        "date": date,
        "url": image_url,
        "is_video": source_type == "video",
    }
    prompt += json.dumps(meta, ensure_ascii=False) + "\n\n"
    if market_name:
        prompt += f"Market context: {market_name}\n\n"
    if ocr_text:
        prompt += f"OCR text: {ocr_text}\n\n"
    prompt += f"Image base64 prefix (truncated): {truncated}\n\nReturn ONLY one valid JSON array (even if empty). Example empty response: []"

    RETRIES = int(os.getenv("LLM_RETRIES", "1"))
    BACKOFF = float(os.getenv("LLM_BACKOFF", "1.0"))

    resp_text = None
    for attempt in range(RETRIES + 1):
        try:
            resp_text = ask_openai(prompt, temperature=0.0)
            break
        except Exception as e:
            # surface exact LLM client error (API key missing, network, import error, etc)
            print(f"LLM call failed (attempt {attempt+1}): {type(e).__name__}: {e}")
            if attempt < RETRIES:
                await asyncio.sleep(BACKOFF * (2 ** attempt))
            else:
                return []

    if not resp_text:
        return []

    resp_text = _strip_code_fences(resp_text)

    # try strict JSON parse first, then salvage
    parsed = None
    try:
        parsed = json.loads(resp_text)
    except Exception as e:
        salvage = _extract_json_array_text(resp_text)
        if salvage:
            try:
                parsed = json.loads(salvage)
            except Exception:
                parsed = None
        if parsed is None:
            preview = (resp_text[:2000] + "...") if isinstance(resp_text, str) else str(resp_text)
            print("LLM response was not valid JSON:", type(e).__name__, e)
            print("LLM response preview:", preview)
            return []

    if isinstance(parsed, list):
        normalized = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            normalized.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "marketPrices": item.get("marketPrices") or [],
                "imageUrl": item.get("imageUrl") or item.get("image_url") or image_url or "",
                "description": item.get("description") or "",
                "source_type": source_type,
                "raw_data": item,
            })
        return normalized

    return []
