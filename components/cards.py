from __future__ import annotations

import json
from typing import Iterable

import streamlit as st


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def info_card(title: str, body: str, tags: Iterable[str] | None = None) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.write(body)
        if tags:
            st.caption(" | ".join(str(tag) for tag in tags))


def status_strip(items: dict[str, str]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items.items(), strict=True):
        col.metric(label, value)


def backend_response_panel(title: str, response: object) -> None:
    if response is None:
        return

    with st.expander(title):
        st.code(json.dumps(response, indent=2, default=str), language="json")


def empty_state(title: str, body: str) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.write(body)
