from __future__ import annotations

import streamlit as st

from components.cards import page_header
from services.backend_placeholders import save_settings


def render_settings() -> None:
    page_header(
        "Settings",
        "Configure local-only behavior, processing defaults, and future backend paths.",
    )

    with st.form("settings"):
        st.subheader("Privacy")
        offline_only = st.toggle("Offline-only mode", value=True)
        telemetry = st.toggle("Usage telemetry", value=False, disabled=True)

        st.subheader("Processing defaults")
        default_subject = st.text_input("Default subject", placeholder="General")
        auto_process = st.toggle("Auto-run AI processing after uploads", value=True)
        model_path = st.text_input("Local model path", placeholder="models/phi-3-mini-q4_k_m.gguf")
        database_path = st.text_input("Database path", placeholder="data/neuronote.db")

        submitted = st.form_submit_button("Save settings", type="primary")

    if submitted:
        result = save_settings(
            {
                "offline_only": offline_only,
                "telemetry": telemetry,
                "default_subject": default_subject,
                "auto_process": auto_process,
                "model_path": model_path,
                "database_path": database_path,
            }
        )
        if result["ok"]:
            st.success(result["message"])
        else:
            st.error(result["message"])
