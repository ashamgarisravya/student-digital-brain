from __future__ import annotations

import streamlit as st


def render_search_controls() -> dict[str, object]:
    query = st.text_input(
        "Search your brain",
        placeholder="Try: photosynthesis definition, thermodynamics derivation, exam formulas",
    )

    cols = st.columns([1, 1, 1])
    subject = cols[0].selectbox("Subject", ["All subjects", "Biology", "Physics", "Chemistry", "Math"])
    source_type = cols[1].selectbox("Source type", ["All types", "Documents", "Images", "Audio", "Text"])
    ranking = cols[2].selectbox("Ranking", ["Most relevant", "Newest", "Needs revision"])

    include_definitions = st.checkbox("Prioritize definitions and key concepts", value=True)
    return {
        "query": query,
        "subject": subject,
        "source_type": source_type,
        "ranking": ranking,
        "include_definitions": include_definitions,
    }
