import os

import streamlit as st
from openai import OpenAI

from prompts import SYSTEM_PROMPT

MODEL = "gpt-4o-mini"


def _get_openai_client():
    try:
        key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        key = None

    if not key:
        key = os.getenv("OPENAI_API_KEY")

    if not key or not key.strip():
        raise ValueError("OPENAI_API_KEY is not set.")

    return OpenAI(api_key=key.strip())

def classify_po(po_description: str, supplier: str = "Not provided"):
    client = _get_openai_client()
    user_prompt = f"""
PO Description:
{po_description}

Supplier:
{supplier}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content
