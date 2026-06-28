from __future__ import annotations

import time

import streamlit as st

from components.cards import backend_response_panel, page_header
from components.notifications import notify_success
from services.backend_placeholders import generate_quiz


def render_quiz() -> None:
    page_header(
        "Quiz Generator",
        "Generate practice questions from stored notes once the backend question service is connected.",
    )

    cols = st.columns([1, 1, 1])
    subject = cols[0].selectbox("Subject", ["Biology", "Physics", "Chemistry", "Math"])
    question_count = cols[1].number_input("Questions", min_value=3, max_value=25, value=5)
    difficulty = cols[2].selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard"])
    modes = st.multiselect("Question types", ["Multiple choice", "Short answer", "Definition recall"], default=["Multiple choice"])

    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []

    if st.button("Generate quiz", type="primary"):
        with st.spinner("Generating questions from local concepts..."):
            time.sleep(0.5)
            questions = generate_quiz(subject, int(question_count), difficulty, modes)
            st.session_state.quiz_questions = questions

        notify_success("Quiz ready.")

    for index, question in enumerate(st.session_state.quiz_questions, start=1):
        with st.container(border=True):
            st.markdown(f"**Q{index}. {question['prompt']}**")
            answer = st.radio("Choose an answer", question["options"], key=f"quiz-{index}")
            if st.button("Check", key=f"check-{index}"):
                if answer == question["answer"]:
                    st.success("Correct.")
                else:
                    st.error(f"Review this: {question['answer']}")
                st.caption(question.get("explanation", ""))
            st.caption(question["source"])
            backend_response_panel("Question backend response", question)
