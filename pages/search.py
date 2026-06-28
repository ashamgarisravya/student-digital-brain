from __future__ import annotations

import time

import streamlit as st

from components.cards import page_header
from components.search_box import render_search_controls
from services.backend_placeholders import search_knowledge_base


def render_search() -> None:
    page_header(
        "Search",
        "Search concepts, definitions, source snippets, and relationships across local study material.",
    )

    controls = render_search_controls()
    if st.button("Search", type="primary"):
        if not str(controls["query"]).strip():
            st.warning("Enter a search query first.")
            return

        with st.spinner("Searching the local knowledge index..."):
            time.sleep(0.4)
            results = search_knowledge_base(controls)

        if not results:
            st.info("No matching results yet. Upload and process study material to populate search.")
            return

        st.success(f"Found {len(results)} relevant results.")
        for item in results:
            with st.container(border=True):
                st.markdown(f"**{item['title']}**")
                st.caption(f"{item['subject']} | {item['source']} | Relevance {item['score']}%")
                st.write(item["snippet"])
                st.button("Open source", key=f"open-{item['id']}")
