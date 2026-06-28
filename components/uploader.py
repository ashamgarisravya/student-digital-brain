from __future__ import annotations

from typing import Iterable

import streamlit as st

from components.notifications import notify_error, notify_success


def render_upload_panel(
    title: str,
    help_text: str,
    accepted_types: Iterable[str],
    upload_kind: str,
    processor,
    max_files: int = 10,
) -> None:
    key_prefix = upload_kind.lower().replace(" ", "-")
    st.subheader(title)
    st.caption(help_text)

    files = st.file_uploader(
        "Drop files here",
        type=list(accepted_types),
        accept_multiple_files=True,
        help=f"Up to {max_files} files can be selected in this frontend.",
        key=f"{key_prefix}-files",
    )

    subject = st.text_input("Subject", placeholder="Example: Biology, Physics, History", key=f"{key_prefix}-subject")
    topic = st.text_input("Topic", placeholder="Example: Chapter 3, Mechanics, Cell structure", key=f"{key_prefix}-topic")
    notes = st.text_area(
        "Notes",
        placeholder="Optional context for the backend processing step.",
        height=90,
        key=f"{key_prefix}-notes",
    )

    disabled = not files
    if st.button("Upload and process", type="primary", disabled=disabled, key=f"{key_prefix}-submit"):
        if len(files) > max_files:
            notify_error(f"Select {max_files} files or fewer.")
            return

        progress = st.progress(0, text="Preparing upload")
        with st.spinner("Sending files to the local processing queue..."):
            results = []
            for index, file in enumerate(files, start=1):
                progress.progress(int(index / len(files) * 100), text=f"Processing {file.name}")
                results.append(
                    processor(
                        file=file,
                        metadata={
                            "kind": upload_kind,
                            "subject": subject,
                            "topic": topic,
                            "notes": notes,
                        },
                    )
                )

        failed = [result for result in results if not result.get("ok", False)]
        if failed:
            notify_error(f"{len(failed)} upload item failed.")
        else:
            notify_success(f"Queued {len(results)} {upload_kind} item(s) for backend processing.")
