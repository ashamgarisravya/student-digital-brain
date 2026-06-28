from __future__ import annotations

import streamlit as st

NAV_ITEMS = [
    "Dashboard",
    "Upload",
    "Search",
    "Quiz Generator",
    "Revision Planner",
    "Settings",
]


def render_sidebar(status: dict[str, object]) -> str:
    with st.sidebar:
        st.markdown("## NeuroNote")
        st.caption("Offline Student Digital Brain")
        st.divider()
        selected = st.radio("Navigation", NAV_ITEMS, label_visibility="collapsed")
        st.divider()
        st.markdown("**Local status**")
        st.caption(f"Mode: {status['mode']}")
        st.caption(f"Backend: {status['backend']}")
        st.caption(f"Last sync: {status['last_sync']}")
        st.divider()
        st.caption("Local Ollama + SQLite backend. Uploaded PDFs are the only knowledge source.")
    return selected
