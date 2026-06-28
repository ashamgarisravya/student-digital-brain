from __future__ import annotations

import time

import streamlit as st

from components.cards import page_header
from components.search_box import render_search_controls
from services.backend_placeholders import search_keyword, search_subject, search_topics


def render_search() -> None:
    page_header(
        "Search",
        "Search concepts, definitions, source snippets, and relationships across local study material.",
    )

    controls = render_search_controls()
    if st.button("Search", type="primary"):
        subject = str(controls["subject"]).strip()
        topic = str(controls["topic"]).strip()
        keyword = str(controls["keyword"]).strip()

        if not any([subject, topic, keyword]):
            st.warning("Enter a subject, topic, or keyword first.")
            return

        with st.spinner("Searching the local knowledge index..."):
            time.sleep(0.4)
            results = []
            if subject:
                results.extend(search_subject(subject, controls))
            if topic:
                results.extend(search_topics(topic, controls))
            if keyword:
                results.extend(search_keyword(keyword, controls))

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
