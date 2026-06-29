from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, empty_state, page_header
from components.notifications import notify_success
from services.backend import generate_revision_plan, get_pdf_options, get_revision_source_data


def render_revision() -> None:
    page_header(
        "Revision Companion",
        "Turn the latest uploaded PDF into a structured study roadmap, notes, and question bank using local Ollama.",
    )

    options = get_pdf_options()
    subjects = options.get("subjects", [])
    if not subjects:
        _render_progress_card(0, 0)
        empty_state("No revision material yet", "Upload and process a class 5-12 study PDF first.")
        return

    cols = st.columns(2)
    subject = cols[0].selectbox("Subject", subjects)
    topics = options.get("topics_by_subject", {}).get(subject, [])
    topic = cols[1].selectbox("Lesson / Unit", topics or ["General"])

    selection_key = f"{subject}|{topic}"
    if st.session_state.get("revision_selection") != selection_key:
        st.session_state.revision_data = get_revision_source_data(subject=subject, topic=topic)
        st.session_state.completed_topics = set()
        st.session_state.revision_selection = selection_key
    if "revision_data" not in st.session_state:
        st.session_state.revision_data = get_revision_source_data(subject=subject, topic=topic)
    if "completed_topics" not in st.session_state:
        st.session_state.completed_topics = set()

    if st.button("Generate / load PDF revision companion", type="primary"):
        with st.spinner("Building revision material from the uploaded PDF..."):
            st.session_state.revision_data = generate_revision_plan(subject=subject, topic=topic)
            st.session_state.completed_topics = set()
        notify_success("Revision companion ready.")

    data = st.session_state.revision_data
    if not data or not data.get("mind_map", {}).get("topics"):
        _render_progress_card(0, 0)
        empty_state("No revision material yet", "Upload and process a study PDF, then generate the revision companion.")
        return

    topics = data.get("mind_map", {}).get("topics", [])
    _render_topic_checklist(topics)
    _render_progress_card(len(topics), len(st.session_state.completed_topics))

    st.subheader("1. Mind Map")
    _render_mind_map(data.get("mind_map", {}))

    st.subheader("2. Important Topics")
    _render_important_topics(data.get("important_topics", []))

    st.subheader("3. Study Notes")
    _render_study_notes(data.get("study_notes", {}))

    st.subheader("4. Question Bank")
    _render_question_bank(data.get("question_bank", {}))

    st.subheader("5. Additional Revision")
    _render_remaining_topics(data)

    backend_response_panel("Revision backend response", data)


def _render_progress_card(total: int, completed: int) -> None:
    remaining = max(0, total - completed)
    completion = int((completed / total) * 100) if total else 0
    with st.container(border=True):
        st.markdown("**Revision Progress**")
        cols = st.columns(4)
        cols[0].metric("Total Topics", str(total))
        cols[1].metric("Topics Completed", str(completed))
        cols[2].metric("Remaining Topics", str(remaining))
        cols[3].metric("Completion", f"{completion}%")
        st.progress(completion)


def _render_topic_checklist(topics: list[object]) -> None:
    with st.expander("Mark topics completed", expanded=False):
        for item in topics:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "Topic"))
            checked = st.checkbox(title, value=title in st.session_state.completed_topics, key=f"topic-done-{title}")
            if checked:
                st.session_state.completed_topics.add(title)
            else:
                st.session_state.completed_topics.discard(title)


def _render_mind_map(mind_map: dict[str, object]) -> None:
    subject = str(mind_map.get("subject", "Subject"))
    chapter = str(mind_map.get("chapter", "Chapter"))
    root = str(mind_map.get("root") or chapter)
    st.markdown(f"**{root}**")
    st.caption(f"Subject: {subject} | Lesson: {chapter}")
    hierarchy = mind_map.get("hierarchy", [])
    if hierarchy:
        st.markdown("**Important Sequence**")
        st.code("\n   ↓\n".join(str(item) for item in hierarchy), language="text")
    for item in mind_map.get("topics", []):
        if not isinstance(item, dict):
            continue
        with st.container(border=True):
            st.markdown(f"**Topic:** {item.get('title', '')}")
            st.write(f"Definition: {item.get('definition', '')}")
            related = item.get("related_concepts", [])
            if related:
                st.caption("Related Concepts: " + " | ".join(str(value) for value in related))


def _render_important_topics(items: list[object]) -> None:
    if not items:
        empty_state("No important topics found", "The uploaded PDF did not produce important-topic cards.")
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        with st.container(border=True):
            st.markdown(f"**{item.get('title', '')}**")
            st.write(str(item.get("explanation", "")))
            if item.get("example"):
                st.info(f"Example: {item.get('example')}")
            st.caption(f"Why important: {item.get('why_important', '')}")


def _render_study_notes(notes: dict[str, object]) -> None:
    if not notes:
        empty_state("No study notes found", "Generate revision after uploading a PDF.")
        return
    tabs = st.tabs([name for name, values in notes.items() if values] or ["Notes"])
    populated = [(name, values) for name, values in notes.items() if values]
    if not populated:
        st.info("No populated note categories were returned.")
        return
    for tab, (name, values) in zip(tabs, populated, strict=False):
        with tab:
            st.markdown(f"**{name}**")
            for value in values:
                st.write(f"- {value}")


def _render_question_bank(bank: dict[str, object]) -> None:
    labels = [
        ("very_short", "Very Short Answer Questions"),
        ("short", "Short Answer Questions"),
        ("long", "Long Answer Questions"),
    ]
    for key, label in labels:
        with st.expander(label, expanded=key == "very_short"):
            items = bank.get(key, []) if isinstance(bank, dict) else []
            if not items:
                st.info("No questions in this category.")
                continue
            for index, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                st.markdown(f"**{index}. {item.get('question', '')}**")
                st.write(f"Answer: {item.get('answer', '')}")
                st.caption(f"Explanation: {item.get('explanation', '')}")


def _render_remaining_topics(data: dict[str, object]) -> None:
    cols = st.columns(3)
    sections = [
        ("Additional Reading", data.get("additional_reading", [])),
        ("Optional Topics", data.get("optional_topics", [])),
        ("Advanced Topics", data.get("advanced_topics", [])),
    ]
    for col, (label, values) in zip(cols, sections, strict=True):
        with col:
            st.markdown(f"**{label}**")
            if not values:
                st.caption("No items.")
                continue
            for value in values:
                st.write(f"- {value}")


if __name__ == "__main__":
    render_revision()
