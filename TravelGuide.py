# TravelGuide.py
# -----------------------------------------------
# AI Travel Guide (Streamlit + OpenAI)
# - Collects travel preferences
# - Calls GPT models with robust fallbacks
# - Renders a structured itinerary on-screen
# - Generates a clean PDF (0.5" left/right margins)
# -----------------------------------------------

import os
from datetime import datetime
from textwrap import dedent

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# PDF generation
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
)

# -------------------------
# ENV & CLIENT
# -------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# STREAMLIT CONFIG
# -------------------------
st.set_page_config(
    page_title="AI Travel Guide",
    page_icon="✈️",
    layout="centered",
)

FORM_KEYS = [
    "destination",
    "days",
    "interests",
    "guardrails",
]

def init_form_state():
    for k in FORM_KEYS:
        if k == "days":
            st.session_state.setdefault(k, 1)
        else:
            st.session_state.setdefault(k, "")
    st.session_state.setdefault("plan_md", "")

def reset_all_callback():
    for k in FORM_KEYS:
        if k == "days":
            st.session_state[k] = 1
        else:
            st.session_state[k] = ""
    st.session_state["plan_md"] = ""
    st.session_state.pop("last_model_used", None)
    st.session_state.pop("last_usage", None)

def clear_fields_only_callback():
    for k in FORM_KEYS:
        if k == "days":
            st.session_state[k] = 1
        else:
            st.session_state[k] = ""

init_form_state()

st.title("✈️ AI Travel Guide")
st.caption("Generate a personalized, day-by-day travel plan with PDF export")

with st.expander("What this app does", expanded=False):
    st.markdown(
        "- Collects your destination and trip duration\n"
        "- Tailors activities based on your **Interests** and **Guardrails**\n"
        "- Produces a **Day-by-Day Itinerary** with travel tips\n"
        "- Lets you **download a PDF** with professional formatting (0.5\" margins)"
    )

# -------------------------
# PROMPTS
# -------------------------
SYSTEM_PROMPT = dedent("""
You are an expert AI TRAVEL GUIDE and itinerary planner.
Requirements:
- Create a realistic, day-by-day travel plan.
- Respect user interests and guardrails strictly.
- Avoid unsafe, inaccessible, or disallowed activities.
- Keep pacing realistic (avoid overloading days).
- Use clear, engaging, travel-friendly language.
Output format in Markdown with these top-level H2 sections (##):
  ## Trip Overview
  ## Day-by-Day Itinerary
  ## Recommended Dining & Local Eats
  ## Travel Tips & Safety Notes
  ## Packing Essentials
""").strip()

def build_user_prompt(destination, days, interests, guardrails):
    return dedent(f"""
    TRAVEL DETAILS
    - Destination: {destination}
    - Number of days: {days}

    INTERESTS
    {interests or 'General sightseeing'}

    GUARDRAILS / CONSTRAINTS
    {guardrails or 'None'}

    INSTRUCTIONS
    - Divide the itinerary clearly by day (Day 1, Day 2, etc.).
    - Suggest kid-friendly and accessible options if requested.
    - Do not violate any stated guardrails.
    - Keep total length readable (≈800–1300 words).
    """).strip()

# -------------------------
# FALLBACKS & EXTRACTOR
# -------------------------
FALLBACK_MODELS = ["gpt-5", "gpt-4o", "gpt-4-turbo"] 

def _extract_text_from_chat_completion(comp):
    try:
        txt = comp.choices[0].message.content
        if isinstance(txt, str) and txt.strip():
            return txt
    except Exception:
        pass
    return ""

def get_plan_markdown(user_prompt):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    last_error = None
    for model_name in FALLBACK_MODELS:
        try:
            comp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_completion_tokens=2000,
            )
            text = _extract_text_from_chat_completion(comp)
            if text.strip():
                st.session_state["last_model_used"] = model_name
                st.session_state["last_usage"] = getattr(comp, "usage", None)
                return text
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All model attempts failed. Last error: {last_error}")

# -------------------------
# PDF HELPERS
# -------------------------
def markdown_to_flowables(md_text, styles):
    flow = []
    body = styles["BodyText"]
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], spaceBefore=8, spaceAfter=4)

    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            flow.append(Spacer(1, 6))
            i += 1
            continue

        if line.startswith("## "):
            flow.append(Paragraph(line[3:].strip(), h2))
            i += 1
            continue
        if line.startswith("### "):
            flow.append(Paragraph(line[4:].strip(), h3))
            i += 1
            continue

        if line.lstrip().startswith(("-", "*", "•")):
            items = []
            while i < len(lines) and lines[i].lstrip().startswith(("-", "*", "•")):
                bullet_text = lines[i].lstrip()[1:].strip()
                items.append(ListItem(Paragraph(bullet_text, body), leftIndent=12))
                i += 1
            flow.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=6))
            flow.append(Spacer(1, 4))
            continue

        flow.append(Paragraph(line, body))
        i += 1

    return flow

def write_pdf(markdown_text, filename="travel_plan.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=LETTER,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Travel Plan",
    )
    styles = getSampleStyleSheet()
    header = ParagraphStyle("Header", parent=styles["Title"], fontSize=18, spaceAfter=12)

    story = []
    story.append(Paragraph("Personalized Travel Plan", header))
    meta = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(meta, styles["Normal"]))
    story.append(Spacer(1, 10))

    story.extend(markdown_to_flowables(markdown_text, styles))
    doc.build(story)
    return filename

# -------------------------
# INPUT FORM
# -------------------------
with st.form("travel_inputs"):
    st.text_input("1) Destination to Travel", placeholder="e.g., Paris, France", key="destination")
    
    st.number_input("2) Number of Days", min_value=1, max_value=30, key="days")

    st.text_area("3) Special Interests", 
                 placeholder="e.g., Museums, Food & Cuisine, Historic sites, Nature", 
                 key="interests")

    st.text_area("4) Guardrails / Constraints", 
                 placeholder="e.g., No walking tours, kid-friendly only, wheelchair accessible", 
                 key="guardrails")

    submitted = st.form_submit_button("Generate Travel Plan")

# -------------------------
# MAIN ACTION
# -------------------------
if submitted:
    if not st.session_state["destination"]:
        st.warning("Please provide a destination.")
    else:
        with st.spinner("Planning your trip..."):
            user_prompt = build_user_prompt(
                st.session_state["destination"],
                st.session_state["days"],
                st.session_state["interests"],
                st.session_state["guardrails"],
            )
            st.session_state["plan_md"] = get_plan_markdown(user_prompt)

# DISPLAY LOGIC (Matches career_coach.py)
if st.session_state["plan_md"].strip():
    st.success("Plan generated!")
    st.caption(f"Model: {st.session_state.get('last_model_used', 'unknown')}")
    
    st.subheader(f"Your Travel Plan for {st.session_state['destination']}")
    st.markdown(st.session_state["plan_md"], unsafe_allow_html=False)

    with st.expander("Show raw text (copy-friendly)"):
        st.text_area("Plan (raw)", st.session_state["plan_md"], height=400)

    # PDF export
    try:
        pdf_path = write_pdf(st.session_state["plan_md"], filename="travel_plan.pdf")
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Travel Plan PDF",
                data=f.read(),
                file_name=f"Travel_Plan_{st.session_state['destination']}.pdf",
                mime="application/pdf",
            )
    except Exception as e:
        st.error(f"PDF generation error: {e}")
else:
    if not submitted:
        st.info("Fill in the fields above and click **Generate Travel Plan**.")

st.divider()
col_a, col_b = st.columns([1, 1])
with col_a:
    st.button("🔁 Reset form + clear plan", type="secondary", on_click=reset_all_callback)
with col_b:
    st.button("🧹 Clear fields only", type="secondary", on_click=clear_fields_only_callback)

# Footnote for PPT generation
st.markdown("---")
st.caption("If you wish to generate a PowerPoint presentation using the text above, please click the PPT icon.")
