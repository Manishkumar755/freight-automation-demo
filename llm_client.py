# llm_client.py
import json
import os
import re

from google import genai
from google.genai import types

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class LLMError(Exception):
    """Raised when the Gemini call or its response has a problem."""


def _parse_json(text: str) -> dict:
    """Parse the model's text as JSON, removing markdown code fences if present."""
    if not text:
        raise LLMError("The model returned an empty response.")
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(f"The response was not valid JSON: {e}") from e


def ask_gemini_json(user_prompt: str, api_key: str | None,
                    system: str | None = None, model: str = DEFAULT_MODEL) -> dict:
    """Send a prompt to Gemini and return the response parsed as a dict."""
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key:
        raise LLMError("No Gemini API key was provided.")

    client = genai.Client(api_key=key)
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        temperature=0,
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=config,
        )
    except Exception as e:
        msg = str(e)
        if "API_KEY_INVALID" in msg or "401" in msg or "403" in msg:
            raise LLMError("The API key is invalid or does not have permission.") from e
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            raise LLMError("Rate limit reached. Please try again after a while.") from e
        raise LLMError(f"Gemini call failed: {msg}") from e

    return _parse_json(response.text)
