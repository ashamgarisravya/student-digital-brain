from __future__ import annotations

import streamlit as st

from components.cards import page_header
from components.uploader import render_upload_panel


def render_upload_documents() -> None:
    page_header(
        "Upload Documents",
        "Queue PDFs, text notes, and markdown files for later extraction and structuring.",
    )
    render_upload_panel(
        title="Document intake",
        help_text="The frontend validates file selection and forwards metadata to the backend upload service.",
        accepted_types=["pdf", "txt", "md"],
        upload_kind="document",
    )

    with st.expander("Document processing preview"):
        st.write("Backend connection point: PDF extraction, text chunking, concept extraction, and SQLite persistence.")


def render_upload_images() -> None:
    page_header(
        "Upload Images",
        "Add handwritten notes, scans, and whiteboard photos for OCR processing later.",
    )
    render_upload_panel(
        title="Image intake",
        help_text="Accepted image files are queued for OCR by the backend when connected.",
        accepted_types=["jpg", "jpeg", "png", "tiff", "bmp"],
        upload_kind="image",
    )

    with st.expander("Image processing preview"):
        st.write("Backend connection point: image cleanup, Tesseract OCR, confidence review, and concept linking.")


def render_upload_audio() -> None:
    page_header(
        "Upload Audio",
        "Add lecture recordings and voice notes for offline transcription later.",
    )
    render_upload_panel(
        title="Audio intake",
        help_text="Audio is queued for Whisper.cpp transcription once the backend service is attached.",
        accepted_types=["mp3", "wav", "m4a", "ogg"],
        upload_kind="audio",
        max_files=5,
    )

    with st.expander("Audio processing preview"):
        st.write("Backend connection point: local transcription, section segmentation, summary extraction, and search indexing.")
