import streamlit as st

from components.sidebar import render_sidebar
from pages.Dashboard import render_dashboard
from pages.Knowledge_Graph import render_graph
from pages.Quiz import render_quiz
from pages.Revision import render_revision
from pages.Search import render_search
from pages.Settings import render_settings
from pages.Upload import render_upload
from services.backend_placeholders import get_app_status


PAGES = {
    "Dashboard": render_dashboard,
    "Upload": render_upload,
    "Search": render_search,
    "Knowledge Graph": render_graph,
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
    st.markdown(
        """
        <style>
        :root {
            --nn-bg: #f7f8f6;
            --nn-ink: #18211f;
            --nn-muted: #63706d;
            --nn-line: #d9ded8;
            --nn-green: #1f7a5a;
            --nn-blue: #2f6f9f;
            --nn-gold: #b7791f;
            --nn-red: #b42318;
        }
        .main .block-container {
            padding-top: 1.7rem;
            padding-bottom: 2.5rem;
            max-width: 1240px;
        }
        section[data-testid="stSidebar"] {
            background: #f2f4f0;
            border-right: 1px solid var(--nn-line);
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--nn-line);
            border-radius: 8px;
            padding: 14px 16px;
        }
        .nn-card {
            background: #ffffff;
            border: 1px solid var(--nn-line);
            border-radius: 8px;
            padding: 18px;
            min-height: 118px;
        }
        .nn-card-title {
            color: var(--nn-ink);
            font-weight: 700;
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }
        .nn-card-body {
            color: var(--nn-muted);
            line-height: 1.45;
            font-size: 0.94rem;
        }
        .nn-pill {
            display: inline-block;
            border: 1px solid var(--nn-line);
            border-radius: 999px;
            padding: 3px 9px;
            margin: 3px 5px 3px 0;
            color: var(--nn-muted);
            font-size: 0.83rem;
            background: #fbfbfa;
        }
        .nn-section-label {
            color: var(--nn-muted);
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    configure_page()
    status = get_app_status()
    selected_page = render_sidebar(status)
    PAGES[selected_page]()


if __name__ == "__main__":
    main()
