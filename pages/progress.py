from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.cards import page_header
from components.progress import render_activity_table, render_subject_progress
from services.backend_placeholders import get_dashboard_data, get_progress_data


def render_progress() -> None:
    page_header(
        "Progress Dashboard",
        "Track study consistency, quiz outcomes, and topic readiness as backend data becomes available.",
    )

    progress_data = get_progress_data()
    dashboard_data = get_dashboard_data()

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Subject readiness")
        render_subject_progress(progress_data["subjects"])

    with right:
        st.subheader("Weekly study minutes")
        chart_data = pd.DataFrame(
            {
                "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "Minutes": [0, 0, 0, 0, 0, 0, 0],
            }
        )
        fig = px.bar(chart_data, x="Day", y="Minutes", color_discrete_sequence=["#1f7a5a"])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Learning history")
    render_activity_table(dashboard_data["recent_activity"])
