"""
Classify an incoming customer email, pick the right team, and draft a reply.
A human approves every reply before it is sent. Drafts never quote a price.
"""
import json
import os

from anthropic import Anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

ROUTING = {
    "quote_request": "sales@yourcompany.example",
    "tracking": "ops@yourcompany.example",
    "documents": "documentation@yourcompany.example",
    "complaint": "customer-service@yourcompany.example",
    "other": "ops-manager@yourcompany.example",
}

SYSTEM = """You triage emails for a freight forwarding company.
Return ONLY a JSON object with keys:
category (one of: quote_request, tracking, documents, complaint, other),
urgency (low, medium, high),
summary (one line),
draft_reply (polite reply in the same language as the email; do NOT state any price, date or commitment that is not in the email; say the team will confirm).
Output raw JSON only."""


def triage(subject: str, body: str) -> dict:
    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Subject: {subject}\n\n{body}"}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "", 1).strip()
    result = json.loads(raw)
    category = result.get("category", "other")
    result["route_to"] = ROUTING.get(category, ROUTING["other"])
    result["status"] = "awaiting_human_approval"
    return result
