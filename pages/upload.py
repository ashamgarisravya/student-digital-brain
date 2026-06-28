from __future__ import annotations

import streamlit as st

from components.cards import page_header
from components.uploader import render_upload_panel
from services.backend_placeholders import process_audio, process_document, process_image


def render_upload() -> None:
    page_header(
        "Upload",
        "Queue PDFs, images, audio, and text for backend processing without changing the UI later.",
    )

    pdf_tab, image_tab, audio_tab, text_tab = st.tabs(["PDF", "Images", "Audio", "Text"])

    with pdf_tab:
        render_upload_panel(
            title="PDF intake",
            help_text="PDF files are passed to process_document().",
            accepted_types=["pdf"],
            upload_kind="PDF",
            processor=process_document,
        )

    with image_tab:
        render_upload_panel(
            title="Image intake",
            help_text="Image files are passed to process_image().",
            accepted_types=["jpg", "jpeg", "png", "tiff", "bmp"],
            upload_kind="image",
            processor=process_image,
        )

    with audio_tab:
        render_upload_panel(
            title="Audio intake",
            help_text="Audio files are passed to process_audio().",
            accepted_types=["mp3", "wav", "m4a", "ogg"],
            upload_kind="audio",
            processor=process_audio,
            max_files=5,
        )

    with text_tab:
        st.subheader("Text intake")
        st.caption("Direct text notes are wrapped and passed to process_document().")
        subject = st.text_input("Subject", key="text-subject", placeholder="Example: Biology")
        topic = st.text_input("Topic", key="text-topic", placeholder="Example: Photosynthesis")
        text = st.text_area("Paste notes", height=220, placeholder="Paste class notes, definitions, or assignment text.")
        if st.button("Save text note", type="primary", disabled=not text.strip()):
            with st.spinner("Sending text to process_document()..."):
                result = process_document(
                    file={"name": "manual-text-note.txt", "content": text},
                    metadata={"kind": "text", "subject": subject, "topic": topic},
                )
            if result.get("ok"):
                st.success("Text note queued for backend processing.")
            else:
                st.error("Text note could not be queued.")
