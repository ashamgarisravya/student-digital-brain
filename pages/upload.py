from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, page_header
from components.notifications import notify_error, notify_success
from components.progress import render_processing_progress
from services.backend import process_document


def render_upload() -> None:
    page_header(
        "Upload",
        "Upload a class 5-12 study PDF and label it by class, subject, and lesson before local AI extraction.",
    )

    file = st.file_uploader("Study PDF", type=["pdf"], accept_multiple_files=False)
    cols = st.columns(3)
    grade = cols[0].selectbox("Class", [str(value) for value in range(5, 13)], index=5)
    subject = cols[1].text_input("Subject", placeholder="Example: Biology")
    topic = cols[2].text_input("Lesson / Unit", placeholder="Example: Unit 1 Diversity")

    can_process = file is not None and subject.strip() and topic.strip()
    if not can_process:
        st.caption(
            "Select a PDF and enter subject plus lesson/unit. These labels are used by Quiz, Revision, and Search."
        )

    if st.button("Extract and process PDF", type="primary", disabled=not can_process):
        progress_slot = st.empty()
        with progress_slot:
            render_processing_progress(10, "Saving PDF locally")
        with st.spinner("Extracting PDF text and asking local Ollama to structure it..."):
            try:
                with progress_slot:
                    render_processing_progress(45, "Extracting text")
                result = process_document(
                    file=file,
                    metadata={"class": grade, "grade": grade, "subject": subject.strip(), "topic": topic.strip()},
                )
                with progress_slot:
                    render_processing_progress(100, "Stored in SQLite")
            except Exception as exc:
                result = {"ok": False, "error": str(exc), "status": "failed"}

        if result.get("ok"):
            if result.get("cache_hit"):
                notify_success("This PDF was already processed. Reused cached SQLite data.")
            else:
                notify_success("PDF processed and stored locally.")
        else:
            notify_error(str(result.get("error", "PDF processing failed.")))
        _render_pdf_summary(result)
        backend_response_panel("PDF processing response", result)


def _render_pdf_summary(result: dict[str, object]) -> None:
    if not result.get("ok"):
        return
    structured = result.get("structured_json", {})
    st.subheader("Extraction result")
    cols = st.columns(4)
    cols[0].metric("Characters", f"{int(result.get('extracted_chars') or 0):,}")
    cols[1].metric("Pages", str(result.get("page_count") or 0))
    cols[2].metric("Topics", str(len(structured.get("topics", [])) if isinstance(structured, dict) else 0))
    cols[3].metric("Cache", "Hit" if result.get("cache_hit") else "New")
    if isinstance(structured, dict) and structured.get("summary"):
        st.info(str(structured["summary"]))


if __name__ == "__main__":
    render_upload()
