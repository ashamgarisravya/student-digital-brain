from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, page_header, status_strip
from neuronote.config import SUPPORTED_OLLAMA_MODELS, get_settings
from neuronote.ollama import ollama_status
from services.backend import get_app_status, save_settings


def render_settings() -> None:
    page_header(
        "Settings",
        "Configure local Ollama, OCR, and SQLite paths for the offline PDF study assistant.",
    )

    status = get_app_status()
    settings = get_settings()
    ollama = ollama_status()
    status_strip({"Mode": str(status["mode"]), "Backend": str(status["backend"]), "Storage": str(status["storage"])})

    with st.form("settings"):
        st.subheader("Ollama")
        model_options = list(SUPPORTED_OLLAMA_MODELS)
        current_model = settings.ollama_model if settings.ollama_model in model_options else model_options[0]
        model = st.selectbox("Model", model_options, index=model_options.index(current_model))
        host = st.text_input("Ollama host", value=settings.ollama_host)
        if ollama.get("available"):
            st.success("Ollama is reachable locally.")
            available = [str(item) for item in ollama.get("models", [])]
            if available:
                st.caption("Installed models: " + " | ".join(available[:8]))
        else:
            st.warning("Ollama is not reachable. Run `ollama serve` and pull a local model before the final demo.")

        st.subheader("PDF extraction")
        st.caption(f"Tesseract path: {settings.tesseract_cmd}")

        st.subheader("Storage")
        database_path = st.text_input("Database path", value=str(settings.database_path))
        uploads_path = st.text_input("Uploads path", value=str(settings.upload_dir))
        offline_only = st.toggle("Offline-only mode", value=True)

        submitted = st.form_submit_button("Save settings", type="primary")

    if submitted:
        result = save_settings(
            {
                "offline_only": offline_only,
                "ollama_model": model,
                "ollama_host": host,
                "database_path": database_path,
                "uploads_path": uploads_path,
            }
        )
        if result["ok"]:
            st.success(result["message"])
        else:
            st.error(result["message"])
        backend_response_panel("Settings backend response", result)


if __name__ == "__main__":
    render_settings()
