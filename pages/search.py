from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, empty_state, page_header
from components.notifications import notify_success
from services.backend import get_pdf_options, search_all


def render_search() -> None:
    page_header(
        "Semantic Search",
        "Search your uploaded textbook PDF by subject, lesson, and keyword.",
    )

    st.info("Answers come only from uploaded PDFs. If the lesson does not contain the keyword, NeuroNote will say so.")

    options = get_pdf_options()
    subjects = options.get("subjects", [])
    if not subjects:
        empty_state("No PDFs uploaded", "Upload a class 5-12 study PDF before searching.")
        return

    cols = st.columns(3)
    subject = cols[0].selectbox("Subject", subjects)
    topics = options.get("topics_by_subject", {}).get(subject, [])
    topic = cols[1].selectbox("Lesson / Unit", topics or ["General"])
    keyword = cols[2].text_input("Keyword")

    if "semantic_search_results" not in st.session_state:
        st.session_state.semantic_search_results = []

    if st.button("Search PDF notes", type="primary"):
        if not keyword.strip():
            st.warning("Enter a keyword to search inside the selected lesson.")
            return
        with st.spinner("Searching with local Ollama over stored PDF text..."):
            results = search_all(
                subject=subject.strip() or None,
                topic=topic.strip() or None,
                keyword=keyword.strip() or None,
            )
        st.session_state.semantic_search_results = results
        if results:
            notify_success("Search complete.")

    results = st.session_state.semantic_search_results
    if not results:
        return

    for result in results:
        with st.container(border=True):
            if not result.get("present"):
                empty_state(
                    "Not found in this PDF lesson",
                    str(result.get("explanation", "The information is not present in the selected uploaded document.")),
                )
                backend_response_panel("Search backend response", result.get("backend_response"))
                continue

            st.markdown(f"**Source:** {result.get('source', 'Uploaded PDF')}")
            if result.get("heading"):
                st.markdown(f"**Where found:** {result.get('heading')}")
            st.markdown("**PDF excerpt:**")
            st.write(str(result.get("excerpt") or result.get("explanation") or ""))
            if result.get("definition"):
                st.write(f"**Definition:** {result.get('definition', '')}")
            examples = result.get("examples", [])
            if examples:
                st.markdown("**Examples**")
                for example in examples:
                    st.write(f"- {example}")
            related = result.get("related_topics", [])
            if related:
                st.caption("Related Topics: " + " | ".join(str(item) for item in related))
            if result.get("cached"):
                st.caption("Loaded from local search cache.")
            backend_response_panel("Search backend response", result.get("backend_response"))


if __name__ == "__main__":
    render_search()
