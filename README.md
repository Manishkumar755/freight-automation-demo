# Prologis Freight Automation Prototype

A small, working prototype of three freight-operations automations, built with Python, Streamlit, and the Claude API.

| # | Tool | What it does | Needs API key? |
|---|------|--------------|----------------|
| 1 | Quote engine | Rate-based quote for Air, By Road, Sea FCL 20', Sea FCL 40'. Air uses chargeable weight (greater of actual and volumetric). | No |
| 2 | Document extraction | Reads an invoice (.txt or text-based .pdf) and returns structured JSON. Validates the output and flags anything uncertain for human review. | Yes |
| 3 | Email triage | Classifies a customer email, picks the owning team, drafts a reply. Drafts containing prices are blocked. A human approves before anything is sent. | Yes |

## Design principles

- **Human in the loop.** Nothing is sent or booked automatically. Approvals are written to an audit log.
- **Never trust model output.** JSON is parsed and validated in code. Missing fields, bad formats, and low confidence (below 0.85) are flagged.
- **Documents are data.** Text inside uploaded documents is wrapped in `<document>` tags, and the instructions tell the model to ignore any instructions inside it.
- **No price in AI drafts.** A rule-based check blocks drafts that contain prices and replaces them with a safe template.
- **Honest data.** All rates in `rates_sample.csv` are sample values, not real pricing.

## Project structure

```
app.py              Streamlit UI (3 tabs)
main.py             Command-line demo runner
quote_engine.py     Rate and volumetric calculation (pure Python, no API)
doc_extractor.py    Claude extraction + validation + review flags
email_triage.py     Claude triage + routing + price guard
rates_sample.csv    Sample rate table
sample_invoice.txt  Sample commercial invoice
tests/              Unit tests (quote, extraction, triage)
run_tests_offline.py  Runs the tests without pytest
```

## Setup

```bash
pip install -r requirements.txt
```

Optional, for the AI tabs:

```bash
export ANTHROPIC_API_KEY="your-key"     # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
```

Never commit your API key to the code or to GitHub.

## Run

```bash
streamlit run app.py          # Web UI
python main.py                # Offline quote demo in terminal
python main.py --llm          # Also runs extraction and triage (needs key)
python run_tests_offline.py   # Tests (or: pytest)
```

## Limitations (stated openly)

- Rates are sample numbers. Real pricing needs the company's rate cards and surcharges.
- Scanned PDFs need OCR first. The reader only works on text-based PDFs.
- Accuracy is not yet measured. Before any live use, build 20 to 30 labelled sample documents and measure field-level accuracy.
- The "send" step is simulated. Connecting it to email or a CRM needs authentication, error handling, and a retry strategy.
- Email routing addresses are placeholders (`example.com`).

## Production path (next steps)

1. Measure accuracy on a labelled set of 20 to 30 real documents, field by field.
2. Replace sample rates with the live rate table, with versioning and effective dates.
3. Add OCR for scanned documents.
4. Move approvals and logs into a database, and add user login and roles.
5. Connect to n8n or the company's email and CRM, with human approval kept as a required step.
