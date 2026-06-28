from __future__ import annotations

import streamlit as st

from components.cards import backend_response_panel, empty_state, page_header
from components.notifications import notify_success
from services.backend import generate_question_bank, get_pdf_options


def render_quiz() -> None:
    page_header(
        "Quiz Generator",
        "Generate level-wise multiple-choice questions from the selected PDF lesson.",
    )

    st.info("Quiz questions are generated only from the uploaded PDF. No predefined or outside questions are used.")

    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []
    if "question_bank" not in st.session_state:
        st.session_state.question_bank = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    options = get_pdf_options()
    subjects = options.get("subjects", [])
    if not subjects:
        empty_state("No PDF available", "Upload and process a class 5-12 study PDF before generating a quiz.")
        return

    cols = st.columns([1, 1, 1, 1])
    subject = cols[0].selectbox("Subject", subjects)
    topics = options.get("topics_by_subject", {}).get(subject, [])
    topic = cols[1].selectbox("Lesson / Unit", topics or ["General"])
    level = cols[2].selectbox(
        "Assessment Level",
        ["Full Assessment", "Beginner", "Intermediate", "Advanced", "Easy", "Medium", "Hard"],
    )
    count_options = {"Beginner": 15, "Intermediate": 25, "Advanced": 30, "Full Assessment": 40, "Easy": 15, "Medium": 20, "Hard": 20}
    question_count = cols[3].number_input(
        "Questions",
        min_value=10,
        max_value=50,
        value=count_options[level],
        step=5,
    )

    if st.button("Generate NEET-style practice set", type="primary"):
        with st.spinner("Preparing original Class 11 Biology questions from the uploaded PDF..."):
            bank = generate_question_bank(subject=subject, topic=topic)
            mcqs = bank.get("mcq", [])
            st.session_state.question_bank = bank
            st.session_state.quiz_questions = _select_mcqs(mcqs, level, int(question_count))
            st.session_state.quiz_submitted = False
        if st.session_state.quiz_questions:
            notify_success("Quiz ready.")
        else:
            empty_state("No PDF available", "Upload and process a PDF before generating a quiz.")

    questions = st.session_state.quiz_questions
    if not questions:
        return

    answers: dict[int, str] = {}
    for index, question in enumerate(questions, start=1):
        with st.container(border=True):
            st.caption(str(question.get("difficulty", "Medium")))
            st.markdown(f"**Q{index}. {question.get('question', '')}**")
            option_map = question.get("options", {})
            labels = [f"{label}. {text}" for label, text in option_map.items()]
            selected = st.radio("Choose one", labels, key=f"quiz-answer-{index}", label_visibility="collapsed")
            answers[index] = selected.split(".", 1)[0] if selected else ""

            if st.session_state.quiz_submitted:
                correct = str(question.get("correct_answer", ""))
                if answers[index] == correct:
                    st.success("Correct")
                else:
                    st.error(f"Correct answer: {correct}. {option_map.get(correct, '')}")
                st.write(str(question.get("explanation", "")))

    if st.button("Submit quiz", type="primary"):
        st.session_state.quiz_submitted = True
        st.rerun()

    if st.session_state.quiz_submitted:
        score = sum(1 for index, question in enumerate(questions, start=1) if answers.get(index) == question.get("correct_answer"))
        percentage = round(score / len(questions) * 100, 1) if questions else 0
        st.subheader("Score")
        cols = st.columns(3)
        cols[0].metric("Correct", f"{score}/{len(questions)}")
        cols[1].metric("Percentage", f"{percentage}%")
        cols[2].metric("Level", _level_label(percentage))
        st.subheader("Difficulty Breakdown")
        for difficulty, values in _score_by_difficulty(questions, answers).items():
            st.progress(values["percentage"], text=f"{difficulty}: {values['correct']}/{values['total']} ({values['percentage']}%)")
        backend_response_panel("Quiz backend response", questions)

    bank = st.session_state.question_bank
    if bank:
        st.divider()
        st.subheader("Practice Question Bank")
        _render_question_section("True / False", bank.get("true_false", []))
        _render_question_section("Fill in the Blanks", bank.get("fill_blanks", []))
        _render_match_section(bank.get("match_following", []))
        _render_question_section("Assertion - Reason", bank.get("assertion_reason", []))
        _render_question_section("Very Short Answer", bank.get("very_short", []))
        _render_question_section("Short Answer", bank.get("short", []))
        _render_question_section("Long Answer", bank.get("long", []))
        _render_question_section("HOTS", bank.get("hots", []))
        backend_response_panel("Full question bank JSON", bank)


def _select_mcqs(mcqs: list[dict[str, object]], level: str, count: int) -> list[dict[str, object]]:
    normalized = level.lower()
    allowed = {
        "beginner": {"Easy"},
        "easy": {"Easy"},
        "intermediate": {"Easy", "Medium"},
        "medium": {"Medium"},
        "advanced": {"Medium", "Hard"},
        "hard": {"Hard"},
    }.get(normalized, {"Easy", "Medium", "Hard"})
    selected = [item for item in mcqs if str(item.get("difficulty", "Medium")) in allowed]
    if len(selected) < count:
        selected = [*selected, *[item for item in mcqs if item not in selected]]
    return [{**item, "index": index} for index, item in enumerate(selected[:count], start=1)]


def _render_question_section(title: str, items: object) -> None:
    rows = items if isinstance(items, list) else []
    if not rows:
        return
    with st.expander(f"{title} ({len(rows)})", expanded=False):
        for index, item in enumerate(rows, start=1):
            if not isinstance(item, dict):
                continue
            st.markdown(f"**Q{index}. {item.get('question', '')}**")
            st.write(f"Answer: {item.get('answer', '')}")
            st.caption(f"Explanation: {item.get('explanation', '')}")


def _render_match_section(items: object) -> None:
    rows = items if isinstance(items, list) else []
    if not rows:
        return
    with st.expander(f"Match the Following ({len(rows)})", expanded=False):
        for item in rows:
            if not isinstance(item, dict):
                continue
            st.markdown(f"**{item.get('question', '')}**")
            col_a = item.get("column_a", [])
            col_b = item.get("column_b", [])
            cols = st.columns(2)
            cols[0].write("Column I")
            cols[1].write("Column II")
            for left, right in zip(col_a, col_b, strict=False):
                cols = st.columns(2)
                cols[0].write(str(left))
                cols[1].write(str(right))
            st.write("Answer:")
            st.json(item.get("answer", {}))
            st.caption(f"Explanation: {item.get('explanation', '')}")


def _score_by_difficulty(questions: list[dict[str, object]], answers: dict[int, str]) -> dict[str, dict[str, int]]:
    rows: dict[str, dict[str, int]] = {}
    for index, question in enumerate(questions, start=1):
        difficulty = str(question.get("difficulty", "Medium"))
        rows.setdefault(difficulty, {"total": 0, "correct": 0, "percentage": 0})
        rows[difficulty]["total"] += 1
        if answers.get(index) == question.get("correct_answer"):
            rows[difficulty]["correct"] += 1
    for values in rows.values():
        values["percentage"] = round(values["correct"] / values["total"] * 100) if values["total"] else 0
    return rows


def _level_label(percentage: float) -> str:
    if percentage >= 85:
        return "Strong"
    if percentage >= 60:
        return "Good"
    if percentage >= 40:
        return "Needs Practice"
    return "Revise Again"


if __name__ == "__main__":
    render_quiz()
