from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, empty_state, info_card, page_header, status_strip
from components.progress import render_activity_table
from services.backend import get_dashboard_stats


def render_dashboard() -> None:
    page_header(
        "Dashboard",
        "Your offline PDF study workspace powered by local Ollama and SQLite.",
    )

    data = get_dashboard_stats()
    status_strip(data["metrics"])

    st.divider()
    left, right = st.columns([1.35, 1])

    with left:
        st.subheader("Recent Uploaded PDFs")
        recent_pdfs = data.get("recent_pdfs", [])
        if not recent_pdfs:
            empty_state("No PDFs uploaded", "Upload a study PDF to unlock quiz, revision, and semantic search.")
        for item in recent_pdfs:
            with st.container(border=True):
                st.markdown(f"**{item.get('name', 'PDF')}**")
                st.caption(f"Subject: {item.get('subject', 'General')} | Topic: {item.get('topic', 'General')}")
                if item.get("summary"):
                    st.write(str(item["summary"])[:400])

        st.subheader("Recent Activity")
        render_activity_table(data["recent_activity"])

    with right:
        st.subheader("Quick Actions")
        info_card("Continue Revision", "Open the revision companion generated from the latest PDF.", ["Revision"])
        info_card("Start Quiz", "Generate or resume the 20-question PDF quiz.", ["20 MCQ"])
        info_card("Search Notes", "Ask local Ollama about definitions, meanings, and topics in the PDF.", ["Semantic"])

        st.subheader("Subjects")
        subjects = data.get("subjects", [])
        if not subjects:
            st.caption("Subjects appear after PDF processing.")
        for subject in subjects:
            st.write(f"- {subject.get('subject', 'General')}")

        st.subheader("Ollama")
        ollama = data.get("ollama", {})
        if ollama.get("available"):
            st.success(f"Connected: {ollama.get('model')}")
        else:
            st.warning("Ollama is not reachable. Start Ollama locally before final demo.")

    backend_response_panel("Dashboard backend response", data)


if __name__ == "__main__":
    render_dashboard()
