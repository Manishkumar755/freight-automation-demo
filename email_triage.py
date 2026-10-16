"""
Customer email triage: category, urgency, routing, and a DRAFT reply.

Safety rules:
  - A human approves every reply before anything is sent. This module never sends email.
  - Drafts must never contain prices. If a draft looks like it contains a price, it is blocked
    and replaced with a safe template.
"""
import json
import os
import re

from doc_extractor import parse_json

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
CATEGORIES = ("quote_request", "tracking", "documents", "complaint", "other")
URGENCIES = ("low", "medium", "high")

# Example routing only. Replace with real team mailboxes.
ROUTING = {
    "quote_request": "sales@example.com",
    "tracking": "ops@example.com",
    "documents": "documentation@example.com",
    "complaint": "customer-service@example.com",
    "other": "ops-manager@example.com",
}

SAFE_FALLBACK_DRAFT = (
    "Thank you for your email. Our team has received your request and will review it "
    "and get back to you shortly."
)

PRICE_PATTERN = re.compile(
    r"(\$|₹|€|£|\b(USD|SGD|INR|EUR|GBP)\b|\d+(\.\d+)?\s*(/|per)\s*(kg|cm|carton|container|pc|cbm))",
    re.IGNORECASE,
)

SYSTEM = f"""You triage emails for a freight forwarding company.
Return ONLY a JSON object with keys:
category (one of: {", ".join(CATEGORIES)}),
urgency (one of: {", ".join(URGENCIES)}),
summary (one line),
draft_reply (polite reply in the same language as the email. Do NOT state any price, rate, date or commitment).
Output raw JSON only."""


def draft_contains_price(text):
    return bool(PRICE_PATTERN.search(text or ""))


def triage(subject, body, client=None):
    if client is None:
        import anthropic
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("Set ANTHROPIC_API_KEY to run email triage.")
        client = anthropic.Anthropic()

    msg = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Subject: {subject}\n\n{body}"}],
    )
    raw = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "text") == "text")
    try:
        data = parse_json(raw)
    except json.JSONDecodeError:
        return {"status": "error", "message": "model did not return valid JSON", "human_review": True}

    category = data.get("category") if data.get("category") in CATEGORIES else "other"
    urgency = data.get("urgency") if data.get("urgency") in URGENCIES else "high"
    draft = data.get("draft_reply", "")

    blocked = draft_contains_price(draft)
    if blocked:
        draft = SAFE_FALLBACK_DRAFT

    return {
        "status": "blocked_price_in_draft" if blocked else "ready_for_review",
        "category": category,
        "urgency": urgency,
        "summary": data.get("summary", ""),
        "routed_to": ROUTING[category],
        "draft_reply": draft,
        "human_review": True,  # always True in this prototype
    }
