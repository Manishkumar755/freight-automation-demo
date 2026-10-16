"""
Demo runner. Quote engine works offline. Document and email parts need ANTHROPIC_API_KEY.
    python main.py
"""
import os
import json

from quote_engine import Shipment, load_rates, quote
from doc_extractor import extract
from email_triage import triage


def run_quote_demo():
    print("\n=== 1. Quote engine (offline) ===")
    rates = load_rates("rates_sample.csv")
    s = Shipment("DEL", "SIN", "air", weight_kg=120, length_cm=100, width_cm=80, height_cm=60, pieces=2)
    print(json.dumps(quote(s, rates), indent=2))
    print(json.dumps(quote(Shipment("DEL", "LHR", "air", weight_kg=50), rates), indent=2))


def run_document_demo():
    print("\n=== 2. Document extraction (Claude) ===")
    with open("sample_invoice.txt", encoding="utf-8") as f:
        print(json.dumps(extract(f.read()), indent=2, ensure_ascii=False))


def run_email_demo():
    print("\n=== 3. Email triage (Claude) ===")
    subject = "Need rate for 2 cartons to Singapore"
    body = "Hi, can you send me the air freight rate for 2 cartons, around 40 kg, Delhi to Singapore? Thanks, Ravi"
    print(json.dumps(triage(subject, body), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run_quote_demo()
    if os.getenv("ANTHROPIC_API_KEY"):
        run_document_demo()
        run_email_demo()
    else:
        print("\nSkipping Claude demos: set ANTHROPIC_API_KEY to run them.")
