# Interviewer Demo Guide (about 6 minutes)

## Before the call
1. `pip install -r requirements.txt`
2. Set `ANTHROPIC_API_KEY` (only needed for tabs 2 and 3).
3. Run `streamlit run app.py` and check that all three tabs load.
4. Keep `README.md` open so you can show the architecture quickly.

## Script

**0:00 to 0:45. Context.**
"This is a prototype of three freight-operations automations. Every rate and email is sample data. The design rule I followed is that a human approves anything that leaves the system."

**0:45 to 2:00. Tab 1, quote engine.**
- Keep the defaults: Air, DEL to SIN, 120 kg, 100 x 80 x 60 cm, 2 pieces.
- Click **Get quote**. Point out that the volumetric weight (160 kg) is higher than the actual weight (120 kg), so the price uses 160 kg.
- Change the mode to **Sea - FCL 40'** and say that the price is a flat container rate, so dimensions do not matter.
- Change the destination to **LHR** and show the "no rate, route to ops" message. Say that the system fails safely instead of guessing.

**2:00 to 3:30. Tab 2, document extraction.**
- Keep "Use sample_invoice.txt" ticked and click **Extract fields**.
- Show the JSON output.
- Point out that the container number is missing in the document, so the result is flagged for human review. Say: "The system does not invent a container number. It asks a person."

**3:30 to 5:00. Tab 3, email triage.**
- Click **Triage email**.
- Show the category, urgency, and routing.
- Point out the draft. Say: "The draft is not allowed to contain a price. If the model writes one, a rule blocks it and replaces it with a safe message."
- Click **Approve and send (simulated)**. Say: "Nothing is actually sent. The approval is logged."

**5:00 to 6:00. Close and limits.**
"I know the limits. The rates are sample values, scanned PDFs need OCR first, and accuracy still needs measuring on 20 to 30 real documents. My next step would be to do that measurement before any live use, then connect the approval step to the company's email or CRM."

## Likely questions and answers

- **"How do you know the extraction is accurate?"**
  "I don't claim it is yet. The code flags uncertain and incomplete results. The next step is a labelled test set of 20 to 30 documents, with field-level accuracy measured before go-live."

- **"Why not let the AI send the emails?"**
  "A wrong price or a wrong commitment sent to a customer is expensive and hard to undo. Automating the draft and the routing saves the time, and a person keeps the final decision."

- **"What about prompt injection in documents?"**
  "The document is passed as data inside tags, the instructions say to ignore instructions inside it, and the output is validated in code. A document cannot change what the system does."

- **"How would this scale?"**
  "Move the rate table and logs to a database, add a queue for documents, and put the approval step in a UI with roles. The core logic is already separated into modules, so each part can be replaced without rewriting the rest."

- **"Why Streamlit?"**
  "It is fast for a demo and easy for a reviewer to run. A production version could use a proper web app or an n8n workflow, and the logic would stay the same."
