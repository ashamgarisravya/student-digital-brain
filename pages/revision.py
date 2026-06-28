from __future__ import annotations

import time

import streamlit as st

from components.cards import backend_response_panel, page_header
from components.notifications import notify_success
from services.backend_placeholders import generate_revision_plan


def render_revision() -> None:
    page_header(
        "Revision Planner",
        "Create a study sequence from subjects, exam dates, and topic confidence.",
    )

    cols = st.columns([1, 1, 1])
    subject = cols[0].selectbox("Subject", ["Biology", "Physics", "Chemistry", "Math", "All subjects"])
    exam_date = cols[1].date_input("Exam date")
    daily_minutes = cols[2].number_input("Daily study minutes", min_value=15, max_value=360, value=90, step=15)
    focus = st.multiselect("Focus areas", ["Definitions", "Derivations", "Diagrams", "Past mistakes", "Weak topics"])

    if "revision_plan" not in st.session_state:
        st.session_state.revision_plan = []

    if st.button("Generate plan", type="primary"):
        with st.spinner("Drafting a revision plan from local study data..."):
            time.sleep(0.5)
            plan = generate_revision_plan(subject, exam_date, daily_minutes, focus)
            st.session_state.revision_plan = plan
        notify_success("Revision plan generated.")

    for day in st.session_state.revision_plan:
        with st.container(border=True):
            st.markdown(f"**{day['day']} - {day['title']}**")
            st.write(day["work"])
            st.progress(day["load"], text=f"{day['minutes']} minutes")
            backend_response_panel("Schedule item backend response", day)
