from __future__ import annotations

import streamlit as st


def notify_success(message: str) -> None:
    st.success(message)
    st.toast(message)


def notify_error(message: str) -> None:
    st.error(message)


def notify_info(message: str) -> None:
    st.info(message)
