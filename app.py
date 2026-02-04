import base64
import json
import os
from datetime import datetime

import streamlit as st

from classifier import classify_po, MODEL

st.set_page_config(page_title="PO Category Classifier", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
if "po_description" not in st.session_state:
    st.session_state.po_description = ""
if "supplier" not in st.session_state:
    st.session_state.supplier = ""
if "example_applied" not in st.session_state:
    st.session_state.example_applied = "Custom"
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_raw" not in st.session_state:
    st.session_state.last_raw = None
if "image_results" not in st.session_state:
    st.session_state.image_results = []
if "image_prompt" not in st.session_state:
    st.session_state.image_prompt = ""

EXAMPLES = {
    "Custom": {"desc": "", "supplier": ""},
    "DocuSign subscription": {
        "desc": "DocuSign Inc - eSignature Enterprise Pro Subscription",
        "supplier": "DocuSign Inc",
    },
    "Business flight": {
        "desc": "Flight ticket for business travel",
        "supplier": "Indigo Airlines",
    },
    "IT hardware": {
        "desc": "Dell Latitude laptops for engineering team",
        "supplier": "Dell",
    },
    "Catering services": {
        "desc": "Catering for quarterly offsite meeting",
        "supplier": "FreshBites Catering",
    },
}

IMAGE_STYLES = [
    "Photorealistic",
    "Cinematic",
    "Editorial illustration",
    "Minimalist",
    "3D render",
    "Pixel art",
    "Watercolor",
]

LIGHTING = ["Soft studio", "Golden hour", "Moody", "Neon", "Natural"]

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

:root {
    --accent: #2f7ff7;
    --accent-2: #10b981;
    --ink: #0f172a;
    --muted: #64748b;
    --panel: #ffffff;
    --soft: #f1f5f9;
    --border: #e2e8f0;
}

.stApp {
    background: radial-gradient(1200px 600px at 10% -10%, #dbeafe 0%, transparent 60%),
                radial-gradient(800px 400px at 90% 0%, #e0e7ff 0%, transparent 55%),
                linear-gradient(180deg, #f8fafc 0%, #ffffff 40%);
}

.header-wrap {
    padding: 18px 22px;
    border-radius: 16px;
    background: var(--panel);
    border: 1px solid var(--border);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    color: #0f172a;
    background: #e2e8f0;
    border: 1px solid #cbd5f5;
}

.badge.green {
    background: #dcfce7;
    border-color: #86efac;
}

.badge.blue {
    background: #dbeafe;
    border-color: #93c5fd;
}

.badge.orange {
    background: #ffedd5;
    border-color: #fdba74;
}

.badge.red {
    background: #fee2e2;
    border-color: #fca5a5;
}

.subtle {
    color: var(--muted);
    font-size: 0.95rem;
}

.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.metric-card {
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
    text-align: center;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: floatIn 0.6s ease both;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
}

.image-card {
    border-radius: 14px;
    border: 1px solid var(--border);
    background: #ffffff;
    padding: 10px;
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
    animation: floatIn 0.6s ease both;
}

@keyframes floatIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.pulse {
    animation: pulse 1.8s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(47, 127, 247, 0.3); }
    50% { box-shadow: 0 0 0 12px rgba(47, 127, 247, 0); }
}

.stButton>button {
    border-radius: 12px;
    background: linear-gradient(135deg, #2563eb 0%, #22c55e 100%);
    color: white;
    border: none;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 20px rgba(37, 99, 235, 0.25);
}

.stTextInput>div>div>input, .stTextArea textarea {
    border-radius: 12px;
    border: 1px solid var(--border);
    background: #ffffff;
}
</style>
    """,
    unsafe_allow_html=True,
)


def status_for(parsed):
    not_sure_count = sum(1 for k in ["L1", "L2", "L3"] if parsed.get(k) == "Not sure")
    if not_sure_count == 0:
        return "Confident", "green"
    if not_sure_count == 1:
        return "Needs review", "orange"
    return "Low confidence", "red"


def get_openai_api_key():
    try:
        key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        key = None

    if not key:
        key = st.session_state.get("openai_api_key", "").strip() or None

    if not key:
        key = os.getenv("OPENAI_API_KEY")

    return key


st.sidebar.title("About")
st.sidebar.caption("Model")
st.sidebar.code(MODEL)

st.sidebar.divider()
st.sidebar.subheader("Quick actions")
selected_example = st.sidebar.selectbox("Examples", list(EXAMPLES.keys()))
if selected_example != "Custom" and st.session_state.example_applied != selected_example:
    st.session_state.po_description = EXAMPLES[selected_example]["desc"]
    st.session_state.supplier = EXAMPLES[selected_example]["supplier"]
    st.session_state.example_applied = selected_example

st.sidebar.toggle("Show instant preview", value=True, key="preview_inline")

st.sidebar.divider()
st.sidebar.subheader("History")
if st.session_state.history:
    history_labels = [
        f"{item['timestamp']} · {item['po_description'][:40]}"
        for item in st.session_state.history
    ]
    selected_history = st.sidebar.selectbox("Load a previous run", history_labels)
    idx = history_labels.index(selected_history)
    if st.sidebar.button("Load selection"):
        st.session_state.po_description = st.session_state.history[idx]["po_description"]
        st.session_state.supplier = st.session_state.history[idx]["supplier"]

    if st.sidebar.button("Clear history"):
        st.session_state.history = []
        st.session_state.last_result = None
        st.session_state.last_raw = None
else:
    st.sidebar.caption("No history yet")

st.markdown(
    """
<div class="header-wrap">
  <div class="badge blue">Enterprise-ready</div>
  <h1 style="margin: 10px 0 6px;">📦 PO L1–L2–L3 Classifier</h1>
  <div class="subtle">Classify purchase order descriptions into L1/L2/L3 categories using the approved taxonomy.</div>
</div>
    """,
    unsafe_allow_html=True,
)

st.write("")

input_tab, results_tab, history_tab, image_tab = st.tabs(
    ["Input", "Results", "History", "Image Studio"]
)

with input_tab:
    left, right = st.columns([2, 1], gap="large")

    with left:
        po_description = st.text_area(
            "PO Description",
            height=170,
            placeholder="e.g., DocuSign eSignature subscription",
            help="Describe one item or service only. Avoid combining multiple line items.",
            key="po_description",
        )

        supplier = st.text_input(
            "Supplier (optional)",
            placeholder="e.g., DocuSign Inc",
            help="Optional: helps improve classification when the description is vague.",
            key="supplier",
        )

        classify = st.button("Classify", type="primary")

        if st.session_state.preview_inline and (st.session_state.last_result or st.session_state.last_raw):
            st.write("")
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("Latest result (preview)")
            if st.session_state.last_result:
                st.json(st.session_state.last_result)
            else:
                st.text(st.session_state.last_raw)
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Tips for best results")
        st.markdown(
            "- Include brand or product names\n"
            "- Keep it to a single item or service\n"
            "- Add the supplier if you know it"
        )
        st.caption("Example: \"Zoom Pro annual subscription\"")
        st.markdown("</div>", unsafe_allow_html=True)

with results_tab:
    if st.session_state.last_result or st.session_state.last_raw:
        st.subheader("Classification Result")
    else:
        st.info("Run a classification to see results here.")

with history_tab:
    if st.session_state.history:
        for item in st.session_state.history:
            st.markdown(
                f"<div class='card' style='margin-bottom: 12px;'>"
                f"<div class='badge green'>{item['timestamp']}</div>"
                f"<p style='margin: 10px 0 6px;'><strong>{item['po_description']}</strong></p>"
                f"<p class='subtle'>Supplier: {item['supplier'] or 'Not provided'}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No history yet. Your past runs will appear here.")

with image_tab:
    st.subheader("Image Studio")
    st.caption("Generate images with OpenAI GPT Image (gpt-image-1).")

    api_key = get_openai_api_key()
    if not api_key:
        st.warning(
            "No OpenAI API key found. Add `OPENAI_API_KEY` to Streamlit secrets or set it as an environment variable. "
            "You can also paste it below for this session only."
        )

    st.text_input(
        "OpenAI API key (session only)",
        type="password",
        key="openai_api_key",
        placeholder="sk-...",
        help="Stored only in this session. For production, use Streamlit secrets or env vars.",
    )

    col_a, col_b = st.columns([2, 1], gap="large")
    with col_a:
        image_prompt = st.text_area(
            "Image prompt",
            height=140,
            placeholder="e.g., A sleek AI dashboard on a glass table, soft daylight, high-end product photography",
            key="image_prompt",
        )
        style = st.selectbox("Style", IMAGE_STYLES)
        lighting = st.selectbox("Lighting", LIGHTING)
        extra = st.text_input("Extra details (optional)", placeholder="e.g., pastel palette, minimal shadows")

    with col_b:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Generation settings")
        size = st.selectbox("Size", ["auto", "1024x1024", "1024x1536", "1536x1024"])
        quality = st.selectbox("Quality", ["auto", "low", "medium", "high"])
        background = st.selectbox("Background", ["auto", "opaque", "transparent"])
        count = st.slider("Images", min_value=1, max_value=4, value=1)
        st.markdown("</div>", unsafe_allow_html=True)

    final_prompt = image_prompt.strip()
    if final_prompt:
        final_prompt = f"{final_prompt}\nStyle: {style}. Lighting: {lighting}."
        if extra.strip():
            final_prompt = f"{final_prompt} Details: {extra.strip()}."

    generate_disabled = not api_key or not final_prompt
    generate = st.button("Generate images", type="primary", disabled=generate_disabled)

    if generate:
        try:
            from openai import OpenAI
        except Exception:
            st.error("OpenAI SDK not installed. Run `pip install openai` and restart the app.")
            generate = False

    if generate:
        with st.spinner("Generating images..."):
            client = OpenAI(api_key=api_key)
            params = {
                "model": "gpt-image-1",
                "prompt": final_prompt,
                "n": count,
            }
            if size != "auto":
                params["size"] = size
            if quality != "auto":
                params["quality"] = quality
            if background != "auto":
                params["background"] = background

            result = client.images.generate(**params)

        images = []
        for item in result.data:
            b64_json = getattr(item, "b64_json", None)
            if not b64_json and isinstance(item, dict):
                b64_json = item.get("b64_json")
            if b64_json:
                images.append(base64.b64decode(b64_json))

        if images:
            st.session_state.image_results.insert(
                0,
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "prompt": final_prompt,
                    "settings": {"size": size, "quality": quality, "background": background},
                    "images": images,
                },
            )

    if st.session_state.image_results:
        latest = st.session_state.image_results[0]
        st.subheader("Latest images")
        st.markdown(
            f"<div class='badge blue'>Prompt</div> {latest['prompt']}",
            unsafe_allow_html=True,
        )

        cols = st.columns(2)
        for idx, img in enumerate(latest["images"]):
            target = cols[idx % 2]
            with target:
                st.markdown("<div class='image-card'>", unsafe_allow_html=True)
                st.image(img, use_container_width=True)
                st.download_button(
                    f"Download image {idx + 1}",
                    data=img,
                    file_name=f"image_{idx + 1}.png",
                    mime="image/png",
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Image history"):
            for item in st.session_state.image_results[1:6]:
                st.write(f"{item['timestamp']} · {item['prompt']}")
    else:
        st.info("Generate your first image to see it here.")

if "classify" in locals() and classify:
    if not po_description.strip():
        st.warning("Please enter a PO description.")
    else:
        with st.spinner("Classifying..."):
            result = classify_po(po_description, supplier)

        try:
            parsed = json.loads(result)
            st.session_state.last_result = parsed
            st.session_state.last_raw = None
            st.session_state.history.insert(
                0,
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "po_description": po_description,
                    "supplier": supplier,
                    "result": parsed,
                },
            )
        except Exception:
            st.session_state.last_result = None
            st.session_state.last_raw = result

if st.session_state.last_result or st.session_state.last_raw:
    with results_tab:
        st.subheader("Classification Result")

        if st.session_state.last_result:
            parsed = st.session_state.last_result
            l1 = parsed.get("L1", "Not sure")
            l2 = parsed.get("L2", "Not sure")
            l3 = parsed.get("L3", "Not sure")
            status_label, status_class = status_for(parsed)

            st.markdown(
                f"<div class='badge {status_class}'>Status: {status_label}</div>",
                unsafe_allow_html=True,
            )

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(
                    f"<div class='metric-card pulse'><div class='badge'>L1</div><h3>{l1}</h3></div>",
                    unsafe_allow_html=True,
                )
            with m2:
                st.markdown(
                    f"<div class='metric-card'><div class='badge'>L2</div><h3>{l2}</h3></div>",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"<div class='metric-card'><div class='badge'>L3</div><h3>{l3}</h3></div>",
                    unsafe_allow_html=True,
                )

            st.write("")
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.json(parsed)
            st.markdown("</div>", unsafe_allow_html=True)

            json_text = json.dumps(parsed, indent=2)
            st.download_button(
                "Download JSON",
                data=json_text,
                file_name="po_classification.json",
                mime="application/json",
            )

            if st.button("Copy JSON"):
                st.text_area("Copy the JSON below", value=json_text, height=200)

        else:
            st.error("Invalid model response. Showing raw output below.")
            st.text(st.session_state.last_raw)
