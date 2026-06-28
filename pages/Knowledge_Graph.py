from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, page_header, status_strip
from components.graph_view import render_graph_view
from services.backend_placeholders import build_knowledge_graph


def render_graph() -> None:
    page_header(
        "Knowledge Graph",
        "Explore how subjects, concepts, documents, and quizzes connect.",
    )

    controls = st.columns([1, 1])
    subject = controls[0].text_input("Subject filter", placeholder="All subjects")
    topic = controls[1].text_input("Topic filter", placeholder="All topics")

    with st.spinner("Building graph visualization..."):
        graph = build_knowledge_graph(subject=subject or None, topic=topic or None)
    status_strip(
        {
            "Nodes": str(len(graph.get("nodes", []))),
            "Links": str(len(graph.get("edges", []))),
            "Source": str(graph.get("backend_function", "backend")),
        }
    )
    render_graph_view(graph)
    backend_response_panel("Graph backend response", graph)
