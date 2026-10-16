import datetime
import json
import os
from pathlib import Path

import streamlit as st

from doc_extractor import extract, read_document
from email_triage import triage
from quote_engine import Shipment, load_rates, quote

BASE = Path(__file__).parent
LOG = BASE / "audit_log.jsonl"
MODE_LABELS = {
    "air": "Air",
    "road": "By Road",
    "fcl20": "Sea - FCL 20'",
    "fcl40": "Sea - FCL 40'",
}


def log_event(event, details):
    record = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "event": event,
        **details,
    }
    with open(LOG, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


st.set_page_config(page_title="Freight Automation Demo", layout="wide")
st.title("Freight Automation Prototype")
st.caption("Sample data only. Outgoing actions require human approval.")

with st.sidebar:
    st.subheader("Settings")
    api_key = st.text_input(
        "Anthropic API key (optional)",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
    )
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
    st.caption("Quotes work without an API key. Document extraction and email triage need one.")

quote_tab, document_tab, email_tab = st.tabs(
    ["1. Quote engine", "2. Document extraction", "3. Email triage"]
)

with quote_tab:
    st.subheader("Rate-based quote")
    rates = load_rates(BASE / "rates_sample.csv")

    col1, col2, col3 = st.columns(3)
    origin = col1.text_input("Origin code", "DEL")
    destination = col2.text_input("Destination code", "SIN")
    mode = col3.selectbox("Mode", list(MODE_LABELS), format_func=lambda item: MODE_LABELS[item])

    col4, col5, col6, col7, col8 = st.columns(5)
    weight = col4.number_input("Actual weight (kg)", min_value=0.0, value=120.0)
    length = col5.number_input("Length (cm)", min_value=0.0, value=100.0)
    width = col6.number_input("Width (cm)", min_value=0.0, value=80.0)
    height = col7.number_input("Height (cm)", min_value=0.0, value=60.0)
    pieces = col8.number_input("Pieces", min_value=1, value=2, step=1)

    st.caption("Sea FCL prices use the container rate, regardless of dimensions or weight.")

    if st.button("Get quote", type="primary"):
        shipment = Shipment(
            origin.strip(),
            destination.strip(),
            mode,
            weight,
            length,
            width,
            height,
            int(pieces),
        )
        try:
            result = quote(shipment, rates)
        except ValueError as error:
            st.error(str(error))
        else:
            if result["status"] == "ok":
                st.success(f'Sample quote: {result["amount"]} {result["currency"]}')
            else:
                st.warning(result["message"])

            st.json(result)
            log_event(
                "quote",
                {
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "status": result["status"],
                },
            )

with document_tab:
    st.subheader("Extract shipping document details")
    st.caption("Results with missing fields or low confidence should be checked manually.")
    upload = st.file_uploader("Upload an invoice (.txt or text-based .pdf)", type=["txt", "pdf"])
    use_sample = st.checkbox("Use sample_invoice.txt", value=True)

    if st.button("Extract fields"):
        try:
            if upload is not None and not use_sample:
                document_text = read_document(upload, upload.name)
            else:
                document_text = read_document(BASE / "sample_invoice.txt")
            result = extract(document_text)
        except RuntimeError as error:
            st.error(str(error))
        else:
            if result["needs_review"]:
                st.warning("Needs human review")
            else:
                st.success("Passed validation")

            if result.get("missing_fields"):
                st.write("Missing required fields:", ", ".join(result["missing_fields"]))

            for problem in result.get("problems", []):
                st.write(f"- {problem}")

            st.json(result.get("data") or {})
            log_event(
                "extraction",
                {
                    "needs_review": result["needs_review"],
                    "problems": result.get("problems", []),
                },
            )

with email_tab:
    st.subheader("Customer email triage")
    st.caption("Classifies the email and drafts a reply. Sending is simulated.")
    subject = st.text_input("Subject", "Need rate for 2 cartons to Singapore")
    body = st.text_area(
        "Email body",
        "Hi, can you send me the air freight rate for 2 cartons, around 40 kg, Delhi to Singapore?",
        height=120,
    )

    if st.button("Triage email"):
        try:
            st.session_state["triage"] = triage(subject, body)
        except RuntimeError as error:
            st.error(str(error))

    result = st.session_state.get("triage")
    if result and result.get("status") != "error":
        col1, col2, col3 = st.columns(3)
        col1.metric("Category", result["category"])
        col2.metric("Urgency", result["urgency"])
        col3.metric("Routed to", result["routed_to"])

        st.write("**Summary:**", result["summary"])

        if result["status"] == "blocked_price_in_draft":
            st.warning("A price was found in the draft, so a safe template was used.")

        st.text_area("Draft reply (editable)", result["draft_reply"], height=140, key="draft")

        if st.button("Approve and send (simulated)"):
            log_event(
                "approved_reply",
                {
                    "category": result["category"],
                    "routed_to": result["routed_to"],
                },
            )
            st.success("Approved. No email was sent; the action was saved to the audit log.")