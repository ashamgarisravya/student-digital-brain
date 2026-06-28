from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def render_graph_view(graph: dict[str, object]) -> None:
    nodes = list(graph.get("nodes", []))
    edges = list(graph.get("edges", []))

    if not nodes:
        st.info("The knowledge graph will appear after backend concept linking returns nodes and edges.")
        return

    position = {node["id"]: node.get("position", [0, 0]) for node in nodes}
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for edge in edges:
        if edge["source"] not in position or edge["target"] not in position:
            continue
        x0, y0 = position[edge["source"]]
        x1, y1 = position[edge["target"]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1.5, color="#a4ada9"),
            hoverinfo="none",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[node.get("position", [0, 0])[0] for node in nodes],
            y=[node.get("position", [0, 0])[1] for node in nodes],
            mode="markers+text",
            text=[node["label"] for node in nodes],
            textposition="top center",
            marker=dict(size=24, color="#2f6f9f", line=dict(width=2, color="#ffffff")),
            hovertext=[f"{node['label']}<br>{node.get('subject', 'Unassigned')}" for node in nodes],
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
