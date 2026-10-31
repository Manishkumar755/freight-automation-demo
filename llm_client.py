# llm_client.py
import json
import os
import re

from openai import OpenAI

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")


class LLMError(Exception):
    """Raised when the LLM call or its response has a problem."""


def _parse_json(text: str) -> dict:
    if not text:
        raise LLMError("The model returned an empty response.")
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(f"The response was not valid JSON: {e}") from e


def ask_gemini_json(user_prompt: str, api_key: str | None,
                    system: str | None = None, model: str = DEFAULT_MODEL) -> dict:
    """Same name and signature as before, so doc_extractor and email_triage need no changes."""
    key = (api_key or os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not key:
        raise LLMError("No OpenRouter API key was provided.")

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
    except Exception as e:
        msg = str(e)
        if "401" in msg or "403" in msg:
            raise LLMError("The API key is invalid or does not have permission.") from e
        if "429" in msg:
            raise LLMError("Rate limit reached. Please try again after a while.") from e
        raise LLMError(f"LLM call failed: {msg}") from e

    return _parse_json(response.choices[0].message.content or "")
