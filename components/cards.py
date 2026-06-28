from __future__ import annotations

import html
from typing import Iterable

import streamlit as st


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def info_card(title: str, body: str, tags: Iterable[str] | None = None) -> None:
    tag_html = ""
    if tags:
        tag_html = "".join(f"<span class='nn-pill'>{html.escape(tag)}</span>" for tag in tags)

    st.markdown(
        f"""
        <div class="nn-card">
            <div class="nn-card-title">{html.escape(title)}</div>
            <div class="nn-card-body">{html.escape(body)}</div>
            <div>{tag_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_strip(items: dict[str, str]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items.items()):
        col.metric(label, value)


def backend_response_panel(title: str, response: object) -> None:
    if response is None:
        return

    with st.expander(title):
        st.json(response)


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="nn-card">
            <div class="nn-card-title">{html.escape(title)}</div>
            <div class="nn-card-body">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
