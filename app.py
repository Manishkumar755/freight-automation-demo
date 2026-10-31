import datetime
import json
import os
from pathlib import Path

import streamlit as st

from doc_extractor import extract, extract_text
from email_triage import triage
from quote_engine import VALID_MODES, Shipment, load_rates, quote
from llm_client import LLMError

BASE = Path(__file__).parent
LOG = BASE / "audit_log.jsonl"
MODE_LABELS = {"air": "Air", "road": "By Road", "fcl20": "Sea - FCL 20'", "fcl40": "Sea - FCL 40'"}


def log_event(event, payload):
    """Append-only audit trail: every quote, extraction and approval is recorded."""
    record = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "event": event, **payload}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


st.set_page_config(page_title="Freight Automation Demo", layout="wide")
st.title("Freight Automation Prototype")
st.caption("Demo project. Rates and emails are sample data. A human approves every outgoing action.")

with st.sidebar:
    st.subheader("Settings")
    try:
        default_key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        default_key = ""
    api_key = st.text_input(
        "OpenRouter API key (optional)",
        value=default_key,
        type="password",
        help="Needed for document extraction and email triage. Create a key at openrouter.ai.",
    )
    st.caption("Quote engine works without a key. Document and email tools need one.")

tab_quote, tab_doc, tab_email = st.tabs(["1. Quote engine", "2. Document extraction", "3. Email triage"])

# ---------- Tab 1: quote engine (offline) ----------
with tab_quote:
    st.subheader("Rate-based quote")
    rates = load_rates(BASE / "rates_sample.csv")

    c1, c2, c3 = st.columns(3)
    origin = c1.text_input("Origin code", "DEL")
    destination = c2.text_input("Destination code", "SIN")
    mode = c3.selectbox("Mode", list(MODE_LABELS), format_func=lambda m: MODE_LABELS[m])

    c4, c5, c6, c7, c8 = st.columns(5)
    weight = c4.number_input("Actual weight (kg)", min_value=0.0, value=120.0)
    length = c5.number_input("Length (cm)", min_value=0.0, value=100.0)
    width = c6.number_input("Width (cm)", min_value=0.0, value=80.0)
    height = c7.number_input("Height (cm)", min_value=0.0, value=60.0)
    pieces = c8.number_input("Pieces", min_value=1, value=2, step=1)
    st.caption("For sea FCL, dimensions and weight do not change the price. The container rate applies.")

    if st.button("Get quote", type="primary"):
        shipment = Shipment(origin.strip(), destination.strip(), mode, weight, length, width, height, int(pieces))
        try:
            result = quote(shipment, rates)
        except ValueError as e:
            st.error(str(e))
        else:
            if result["status"] == "ok":
                st.success(f"Sample quote: {result['amount']} {result['currency']}")
            else:
                st.warning(result["message"])
            st.json(result)
            log_event("quote", {"origin": origin, "destination": destination, "mode": mode, "status": result["status"]})

#---------- Tab 2: document extraction  ----------
with tab_doc:
    st.subheader("Shipping document to structured data")
    st.caption("Extracts fields into JSON. Low-confidence or incomplete results are flagged for human review.")

    uploaded_file = st.file_uploader(
        "Upload invoice (.txt or text-based .pdf)",
        type=["txt", "pdf"],
    )
    use_sample = st.checkbox("Use sample_invoice.txt")
    sample_text = (BASE / "sample_invoice.txt").read_text(encoding="utf-8") if use_sample else None

    if st.button("Extract fields"):
        try:
            if uploaded_file is not None:
                result = extract(uploaded_file, filename=uploaded_file.name, api_key=api_key)
            elif sample_text is not None:
                result = extract_text(sample_text, api_key=api_key)
            else:
                st.info("Upload a file or tick 'Use sample_invoice.txt' first.")
                result = None

            if result is not None:
                st.json(result)
                if result["needs_review"]:
                    st.warning("Some fields are missing or confidence is low. Human review is required.")
        except LLMError as e:
            st.error(str(e))

# ---------- Tab 3: email triage ( human approval) ----------
with tab_email:
    st.subheader("Customer email triage")
    st.caption("Classifies the email, routes it, and drafts a reply. Nothing is sent until a human approves.")
    subject = st.text_input("Subject", "Need rate for 2 cartons to Singapore")
    body = st.text_area("Email body", "Hi, can you send me the air freight rate for 2 cartons, around 40 kg, Delhi to Singapore?", height=120)

    if st.button("Triage email"):
        try:
            st.session_state["triage"] = triage(subject, body)
        except RuntimeError as e:
            st.error(str(e))

    res = st.session_state.get("triage")
    if res and res.get("status") != "error":
        a, b, c = st.columns(3)
        a.metric("Category", res["category"])
        b.metric("Urgency", res["urgency"])
        c.metric("Routed to", res["routed_to"])
        st.write("**Summary:**", res["summary"])
        if res["status"] == "blocked_price_in_draft":
            st.warning("The AI draft contained a price, so it was replaced with a safe template.")
        st.text_area("Draft reply (editable)", res["draft_reply"], height=140, key="draft")
        if st.button("Approve and send (simulated)"):
            log_event("approved_reply", {"category": res["category"], "routed_to": res["routed_to"]})
            st.success("Approved. Demo only: no email was sent. The approval is written to the audit log.")
