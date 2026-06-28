from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, page_header, status_strip
from services.backend_placeholders import get_app_status, save_settings


def render_settings() -> None:
    page_header(
        "Settings",
        "Configure local-only behavior, processing defaults, and future backend paths.",
    )

    status = get_app_status()
    status_strip({"Mode": str(status["mode"]), "Backend": str(status["backend"]), "Storage": str(status["storage"])})

    with st.form("settings"):
        st.subheader("Model selection")
        model = st.selectbox("Local model", ["Phi-3 Mini GGUF", "TinyLlama GGUF", "Custom GGUF"])
        model_path = st.text_input("Model path", placeholder="models/phi-3-mini-q4_k_m.gguf")

        st.subheader("OCR status")
        ocr_status = st.selectbox("Tesseract OCR", ["Not connected", "Available", "Needs configuration"])

        st.subheader("Storage location")
        database_path = st.text_input("Database path", placeholder="data/neuronote.db")
        uploads_path = st.text_input("Uploads path", placeholder="data/uploads")

        st.subheader("Application information")
        offline_only = st.toggle("Offline-only mode", value=True)
        app_version = st.text_input("Version", value="1.0.0", disabled=True)

        submitted = st.form_submit_button("Save settings", type="primary")

    if submitted:
        result = save_settings(
            {
                "offline_only": offline_only,
                "model": model,
                "model_path": model_path,
                "ocr_status": ocr_status,
                "database_path": database_path,
                "uploads_path": uploads_path,
                "app_version": app_version,
            }
        )
        if result["ok"]:
            st.success(result["message"])
        else:
            st.error(result["message"])
        backend_response_panel("Settings backend response", result)
