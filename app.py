import streamlit as st
import json
from classifier import classify_po, MODEL

st.set_page_config(page_title="PO Category Classifier", layout="centered")

st.title("📦 PO L1–L2–L3 Classifier")

st.sidebar.title("About")
st.sidebar.caption("Model")
st.sidebar.code(MODEL)

st.write("Enter a purchase order description and optionally the supplier to classify it into L1/L2/L3 categories.")

po_description = st.text_area(
    "PO Description",
    height=120,
    placeholder="e.g., DocuSign eSignature subscription",
    help="Describe the item or service clearly. Avoid combining multiple items in one description."
)

supplier = st.text_input(
    "Supplier (optional)",
    placeholder="e.g., DocuSign Inc",
    help="Optional: helps improve classification when the description is vague."
)

if st.button("Classify"):
    if not po_description.strip():
        st.warning("Please enter a PO description.")
    else:
        with st.spinner("Classifying..."):
            result = classify_po(po_description, supplier)

        with st.container():
            st.subheader("Classification Result")
            try:
                st.json(json.loads(result))
            except Exception:
                st.error("Invalid model response")
                st.text(result)
