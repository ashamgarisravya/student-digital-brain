from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components.cards import page_header
from services.backend_placeholders import get_graph_preview


def render_graph() -> None:
    page_header(
        "Knowledge Graph",
        "Explore how subjects, concepts, documents, and quizzes connect.",
    )

    graph = get_graph_preview()
    subjects = ["All subjects"] + sorted({node["subject"] for node in graph["nodes"]})
    selected_subject = st.selectbox("Subject", subjects)
    minimum_strength = st.slider("Minimum link strength", 0, 100, 30)

    nodes = [
        node
        for node in graph["nodes"]
        if selected_subject == "All subjects" or node["subject"] == selected_subject
    ]
    node_ids = {node["id"] for node in nodes}
    edges = [
        edge
        for edge in graph["edges"]
        if edge["source"] in node_ids and edge["target"] in node_ids and edge["strength"] >= minimum_strength
    ]

    position = {node["id"]: node["position"] for node in nodes}
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for edge in edges:
        x0, y0 = position[edge["source"]]
        x1, y1 = position[edge["target"]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = [node["position"][0] for node in nodes]
    node_y = [node["position"][1] for node in nodes]
    labels = [node["label"] for node in nodes]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1.6, color="#9aa6a1"), hoverinfo="none"))
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=labels,
            textposition="top center",
            marker=dict(size=22, color="#2f6f9f", line=dict(width=2, color="#ffffff")),
            hovertext=[f"{node['label']}<br>{node['subject']}" for node in nodes],
            hoverinfo="text",
        )
    )
    fig.update_layout(
        height=560,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Graph data is mocked in the frontend layer and ready to be replaced by backend graph output.")
