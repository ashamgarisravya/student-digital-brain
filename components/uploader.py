from __future__ import annotations

import time
from typing import Iterable

import streamlit as st

from services.backend_placeholders import queue_upload


def render_upload_panel(
    title: str,
    help_text: str,
    accepted_types: Iterable[str],
    upload_kind: str,
    max_files: int = 10,
) -> None:
    st.subheader(title)
    st.caption(help_text)

    files = st.file_uploader(
        "Drop files here",
        type=list(accepted_types),
        accept_multiple_files=True,
        help=f"Up to {max_files} files can be selected in this frontend.",
    )

    subject = st.text_input("Subject", placeholder="Example: Biology, Physics, History")
    tags = st.text_input("Tags", placeholder="exam, chapter-3, definitions")
    run_ai = st.checkbox("Run AI extraction after upload", value=True)

    disabled = not files
    if st.button("Upload and process", type="primary", disabled=disabled):
        if len(files) > max_files:
            st.error(f"Select {max_files} files or fewer.")
            return

        with st.spinner("Sending files to the local processing queue..."):
            time.sleep(0.5)
            result = queue_upload(
                files=files,
                upload_kind=upload_kind,
                subject=subject,
                tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
                run_ai=run_ai,
            )

        if result["ok"]:
            st.success(result["message"])
            st.toast(result["message"])
        else:
            st.error(result["message"])
