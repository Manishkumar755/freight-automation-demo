"""
Extract structured fields from a shipping document using Claude.
Output is validated and flagged for human review when confidence is low or fields are missing.
"""
import json
from anthropic import Anthropic  # pip install anthropic
import os

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
REVIEW_THRESHOLD = 0.85
REQUIRED = ["document_type", "shipper", "consignee", "description", "gross_weight_kg", "invoice_number"]

SYSTEM = """You extract data from freight shipping documents (invoices, packing lists, bills of lading, delivery orders).
Return ONLY a JSON object with these keys:
document_type, shipper, consignee, hs_code, description, gross_weight_kg, packages,
container_number, invoice_number, invoice_date, confidence, missing_fields.

Rules:
- Use null for anything not present in the document. Never guess.
- gross_weight_kg must be a number in kg.
- confidence is a number from 0 to 1 for how sure you are overall.
- missing_fields is a list of REQUIRED keys that are null. Required keys: """ + ", ".join(REQUIRED) + """
- Output raw JSON only. No markdown, no explanation."""


def extract(document_text: str) -> dict:
    try:
        Anthropic = importlib.import_module("anthropic").Anthropic
    except ImportError as e:
        raise RuntimeError("The Anthropic SDK is required; install it with 'pip install anthropic'.") from e
    client = Anthropic()  # reads ANTHROPIC_API_KEY from environment
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM,
        messages=[{"role": "user", "content": document_text}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "", 1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"needs_review": True, "error": f"Invalid JSON from model: {e}", "raw": raw}

    data["needs_review"] = data.get("confidence", 0) < REVIEW_THRESHOLD or bool(data.get("missing_fields"))
    return data


def read_pdf_text(path: str) -> str:
    from pypdf import PdfReader  # pip install pypdf
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
