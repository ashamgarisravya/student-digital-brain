import streamlit as st

from components.sidebar import render_sidebar
from pages.dashboard import render_dashboard
from pages.quiz import render_quiz
from pages.revision import render_revision
from pages.search import render_search
from pages.settings import render_settings
from pages.upload import render_upload
from services.backend import get_app_status

PAGES = {
    "Dashboard": render_dashboard,
    "Upload": render_upload,
    "Search": render_search,
    "Quiz Generator": render_quiz,
    "Revision Planner": render_revision,
    "Settings": render_settings,
}


def configure_page() -> None:
    st.set_page_config(
        page_title="NeuroNote",
        page_icon=":brain:",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def main() -> None:
    configure_page()
    status = get_app_status()
    selected_page = render_sidebar(status)
    PAGES[selected_page]()


if __name__ == "__main__":
    main()
