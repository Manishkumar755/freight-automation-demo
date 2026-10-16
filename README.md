# Prologis Freight: Automation Prototype

Three small building blocks for freight operations, built as an interview demo.

| File | What it does |
|---|---|
| `quote_engine.py` | Rate-table quote for air (chargeable weight) and sea (per container). Unknown lanes go to manual review. |
| `doc_extractor.py` | Sends invoice/BL text to Claude, gets structured JSON, flags low-confidence results for human review. |
| `email_triage.py` | Classifies an email, routes it to a team, drafts a reply. Replies require human approval. |
| `main.py` | Runs all three demos. |

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here      # Windows PowerShell: $env:ANTHROPIC_API_KEY="your_key_here"
python main.py
```

The quote demo runs without an API key. The Claude demos are skipped unless the key is set.

## Design choices to explain in the interview

- **No guessed prices.** The quote engine returns `manual_review` for unknown lanes instead of inventing a rate.
- **Human in the loop.** Document extraction flags `needs_review` when confidence is below 0.85 or required fields are missing. Email drafts are never sent automatically.
- **Structured output.** Every LLM call asks for JSON and validates it, so downstream code (Excel, DB, n8n) can rely on the shape.
- **Model is configurable.** Set `CLAUDE_MODEL` to change it without editing code.

## Connecting to n8n (for the demo)

1. **Gmail Trigger** node: fires on new email to the ops inbox.
2. **HTTP Request** node: sends subject and body to a small Flask/FastAPI wrapper around `email_triage.triage()`.
3. **Switch** node: branches on `category`.
4. **Gmail** node: sends the draft to the routed team for approval, not to the customer.
5. **Google Sheets** node: logs every email with category, urgency, and status.

## Limitations (say these openly)

- Rates in `rates_sample.csv` are made up for the demo.
- Scanned PDFs need OCR before extraction. `read_pdf_text` only works on text-based PDFs.
- Accuracy needs testing on real documents. Build a set of 20 to 30 labelled samples and measure field-level accuracy before any automation goes live.
