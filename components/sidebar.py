from __future__ import annotations

import streamlit as st


NAV_ITEMS = [
    "Dashboard",
    "Upload",
    "Search",
    "Knowledge Graph",
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
        st.caption("Frontend-only app. Backend functions are isolated in `services/backend_placeholders.py`.")
    return selected
