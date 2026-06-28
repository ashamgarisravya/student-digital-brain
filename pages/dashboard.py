from __future__ import annotations

import streamlit as st

from components.cards import info_card, page_header, status_strip
from components.progress import render_activity_table, render_subject_progress
from services.backend_placeholders import get_dashboard_data, get_progress_data


def render_dashboard() -> None:
    page_header(
        "Home Dashboard",
        "A calm command center for uploads, search, revision, and learning progress.",
    )

    data = get_dashboard_data()
    status_strip(data["metrics"])

    st.divider()
    left, right = st.columns([1.35, 1])

    with left:
        st.subheader("Today")
        cols = st.columns(3)
        with cols[0]:
            info_card("Upload", "Add PDFs, images, or lecture audio to the local processing queue.", ["PDF", "OCR", "Audio"])
        with cols[1]:
            info_card("Search", "Find concepts, definitions, and source material across your knowledge base.", ["FTS ready"])
        with cols[2]:
            info_card("Revise", "Turn stored concepts into study sessions and quizzes.", ["Planner", "Quiz"])

        st.subheader("Recent activity")
        render_activity_table(data["recent_activity"])

    with right:
        st.subheader("Progress")
        progress_data = get_progress_data()
        render_subject_progress(progress_data["subjects"])
        st.divider()
        st.subheader("Next actions")
        for action in data["next_actions"]:
            st.checkbox(action, value=False)
