"""
Command-line demo runner.

  python main.py          -> offline quote demo (no API key needed)
  python main.py --llm    -> also runs document extraction and email triage (needs ANTHROPIC_API_KEY)
"""
import argparse
import json
import os
from pathlib import Path

from quote_engine import Shipment, load_rates, quote

BASE = Path(__file__).parent


def run_quote_demo():
    print("\n== 1. Quote engine (offline) ==")
    rates = load_rates(BASE / "rates_sample.csv")
    cases = [
        Shipment("DEL", "SIN", "air", weight_kg=120, length_cm=100, width_cm=80, height_cm=60, pieces=2),
        Shipment("DEL", "KTM", "road", weight_kg=120),
        Shipment("INNSA", "CNSHA", "fcl40"),
        Shipment("DEL", "LHR", "air", weight_kg=50),
    ]
    for s in cases:
        print(f"\n{s.origin} -> {s.destination} | {s.mode}")
        print(json.dumps(quote(s, rates), indent=2))


def run_llm_demo():
    from doc_extractor import extract, read_document
    from email_triage import triage

    print("\n== 2. Document extraction (Claude) ==")
    text = read_document(BASE / "sample_invoice.txt")
    print(json.dumps(extract(text), indent=2, ensure_ascii=False))

    print("\n== 3. Email triage (Claude) ==")
    subject = "Need rate for 2 cartons to Singapore"
    body = "Hi, can you send me the air freight rate for 2 cartons, around 40 kg, Delhi to Singapore?"
    print(json.dumps(triage(subject, body), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true")
    args = ap.parse_args()
    run_quote_demo()
    if args.llm:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("\nSkipping LLM steps: set ANTHROPIC_API_KEY first.")
        else:
            run_llm_demo()
