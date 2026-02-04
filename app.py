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
if "pending_generate" not in st.session_state:
    st.session_state.pending_generate = False

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
MOODS = ["Crisp", "Warm", "Playful", "Elegant", "Futuristic", "Calm"]
COMPOSITIONS = ["Wide shot", "Close-up", "Top-down", "Rule of thirds", "Symmetric"]

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
    --muted: #475569;
    --panel: #ffffff;
    --soft: #f1f5f9;
    --border: #e2e8f0;
    --input-bg: #ffffff;
    --input-text: #0f172a;
}

@media (prefers-color-scheme: dark) {
    :root {
        --accent: #60a5fa;
        --accent-2: #34d399;
        --ink: #e2e8f0;
        --muted: #94a3b8;
        --panel: #0f172a;
        --soft: #111827;
        --border: #1f2937;
        --input-bg: #0b1220;
        --input-text: #e2e8f0;
    }
}

.stApp {
    background: radial-gradient(1200px 600px at 10% -10%, rgba(59, 130, 246, 0.18) 0%, transparent 60%),
                radial-gradient(800px 400px at 90% 0%, rgba(99, 102, 241, 0.16) 0%, transparent 55%),
                linear-gradient(180deg, var(--soft) 0%, transparent 60%);
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
    color: var(--ink);
    background: var(--soft);
    border: 1px solid var(--border);
}

.badge.green { background: #dcfce7; border-color: #86efac; color: #14532d; }
.badge.blue { background: #dbeafe; border-color: #93c5fd; color: #1e3a8a; }
.badge.orange { background: #ffedd5; border-color: #fdba74; color: #7c2d12; }
.badge.red { background: #fee2e2; border-color: #fca5a5; color: #7f1d1d; }

@media (prefers-color-scheme: dark) {
    .badge.green { background: #052e16; border-color: #166534; color: #86efac; }
    .badge.blue { background: #0b1f3a; border-color: #1d4ed8; color: #93c5fd; }
    .badge.orange { background: #3a1c07; border-color: #ea580c; color: #fdba74; }
    .badge.red { background: #3a0b0b; border-color: #dc2626; color: #fca5a5; }
}

.subtle { color: var(--muted); font-size: 0.95rem; }

.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.metric-card {
    background: var(--soft);
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
    background: var(--panel);
    padding: 10px;
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
    animation: floatIn 0.6s ease both;
}

@keyframes floatIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.pulse { animation: pulse 1.8s ease-in-out infinite; }

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

label, .stMarkdown, .stCaption, .stTextInput label, .stTextArea label {
    color: var(--ink) !important;
}

.stTextInput>div>div>input, .stTextArea textarea, .stSelectbox>div>div>div, .stTextInput input {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
}

::placeholder { color: var(--muted) !important; }
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


def build_prompt(subject, style, lighting, mood, composition, extra, negative):
    prompt = f"Subject: {subject}\nStyle: {style}. Lighting: {lighting}. Mood: {mood}. Composition: {composition}."
    if extra.strip():
        prompt = f"{prompt} Extra: {extra.strip()}."
    if negative.strip():
        prompt = f"{prompt} Negative: {negative.strip()}."
    return prompt


def run_image_generation(api_key, prompt, size, quality, background, count, seed):
    try:
        from openai import OpenAI
    except Exception:
        st.error("OpenAI SDK not installed. Run `pip install openai` and restart the app.")
        return None

    client = OpenAI(api_key=api_key)
    params = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": count,
    }
    if size != "auto":
        params["size"] = size
    if quality != "auto":
        params["quality"] = quality
    if background != "auto":
        params["background"] = background
    if seed:
        params["seed"] = seed

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
                "prompt": prompt,
                "settings": {
                    "size": size,
                    "quality": quality,
                    "background": background,
                    "count": count,
                    "seed": seed,
                },
                "inputs": {
                    "subject": st.session_state.image_subject,
                    "style": st.session_state.image_style,
                    "lighting": st.session_state.image_lighting,
                    "mood": st.session_state.image_mood,
                    "composition": st.session_state.image_composition,
                    "extra": st.session_state.image_extra,
                    "negative": st.session_state.image_negative,
                },
                "images": images,
            },
        )

    return images


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
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Prompt Builder")
        subject = st.text_area(
            "Subject",
            height=110,
            placeholder="e.g., A sleek AI dashboard on a glass table",
            key="image_subject",
        )
        style = st.selectbox("Style", IMAGE_STYLES, key="image_style")
        lighting = st.selectbox("Lighting", LIGHTING, key="image_lighting")
        mood = st.selectbox("Mood", MOODS, key="image_mood")
        composition = st.selectbox("Composition", COMPOSITIONS, key="image_composition")
        extra = st.text_input("Extra details (optional)", key="image_extra", placeholder="e.g., pastel palette")
        negative = st.text_input(
            "Negative prompt (optional)",
            key="image_negative",
            placeholder="e.g., text, watermark, logo",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Variation settings")
        size = st.selectbox("Size", ["auto", "1024x1024", "1024x1536", "1536x1024"], key="image_size")
        quality = st.selectbox("Quality", ["auto", "low", "medium", "high"], key="image_quality")
        background = st.selectbox("Background", ["auto", "opaque", "transparent"], key="image_background")
        count = st.slider("Images", min_value=1, max_value=4, value=1, key="image_count")
        seed = st.text_input("Seed (optional)", key="image_seed", placeholder="e.g., 42")
        st.markdown("</div>", unsafe_allow_html=True)

    final_prompt = subject.strip()
    if final_prompt:
        final_prompt = build_prompt(subject, style, lighting, mood, composition, extra, negative)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Prompt preview")
    if final_prompt:
        st.code(final_prompt)
    else:
        st.caption("Add a subject to build the prompt preview.")
    st.markdown("</div>", unsafe_allow_html=True)

    generate_disabled = not api_key or not final_prompt
    generate = st.button("Generate images", type="primary", disabled=generate_disabled)

    if st.session_state.pending_generate and api_key:
        generate = True
        st.session_state.pending_generate = False

    if generate:
        with st.spinner("Generating images..."):
            run_image_generation(
                api_key=api_key,
                prompt=final_prompt,
                size=size,
                quality=quality,
                background=background,
                count=count,
                seed=seed.strip() or None,
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

        st.write("")
        st.subheader("Image history")
        history_cols = st.columns(2)
        for idx, item in enumerate(st.session_state.image_results[:6]):
            target = history_cols[idx % 2]
            with target:
                st.markdown("<div class='image-card'>", unsafe_allow_html=True)
                st.caption(item["timestamp"])
                st.image(item["images"][0], use_container_width=True)
                st.markdown(f"**{item['prompt'][:80]}**")
                if st.button("Reuse settings", key=f"reuse_{idx}"):
                    inputs = item.get("inputs", {})
                    st.session_state.image_subject = inputs.get("subject", "")
                    st.session_state.image_style = inputs.get("style", IMAGE_STYLES[0])
                    st.session_state.image_lighting = inputs.get("lighting", LIGHTING[0])
                    st.session_state.image_mood = inputs.get("mood", MOODS[0])
                    st.session_state.image_composition = inputs.get("composition", COMPOSITIONS[0])
                    st.session_state.image_extra = inputs.get("extra", "")
                    st.session_state.image_negative = inputs.get("negative", "")
                    settings = item.get("settings", {})
                    st.session_state.image_size = settings.get("size", "auto")
                    st.session_state.image_quality = settings.get("quality", "auto")
                    st.session_state.image_background = settings.get("background", "auto")
                    st.session_state.image_count = settings.get("count", 1)
                    st.session_state.image_seed = settings.get("seed", "")
                    st.session_state.pending_generate = False
                if st.button("Regenerate", key=f"regen_{idx}"):
                    inputs = item.get("inputs", {})
                    st.session_state.image_subject = inputs.get("subject", "")
                    st.session_state.image_style = inputs.get("style", IMAGE_STYLES[0])
                    st.session_state.image_lighting = inputs.get("lighting", LIGHTING[0])
                    st.session_state.image_mood = inputs.get("mood", MOODS[0])
                    st.session_state.image_composition = inputs.get("composition", COMPOSITIONS[0])
                    st.session_state.image_extra = inputs.get("extra", "")
                    st.session_state.image_negative = inputs.get("negative", "")
                    settings = item.get("settings", {})
                    st.session_state.image_size = settings.get("size", "auto")
                    st.session_state.image_quality = settings.get("quality", "auto")
                    st.session_state.image_background = settings.get("background", "auto")
                    st.session_state.image_count = settings.get("count", 1)
                    st.session_state.image_seed = settings.get("seed", "")
                    st.session_state.pending_generate = True
                st.markdown("</div>", unsafe_allow_html=True)
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
