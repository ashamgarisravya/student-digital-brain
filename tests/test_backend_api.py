from __future__ import annotations

import fitz

from neuronote.api import (
    generate_quiz,
    generate_revision_plan,
    get_dashboard_stats,
    process_audio,
    process_document,
    process_image,
    search_all,
)
from neuronote.database import reset_database


def _make_pdf(path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_pdf_processing_cache_search_quiz_revision_dashboard(tmp_path):
    db_path = tmp_path / "neuronote.db"
    pdf_path = tmp_path / "biology.pdf"
    reset_database(db_path)
    _make_pdf(pdf_path, "Photosynthesis uses chlorophyll to convert light energy into chemical energy.")

    first = process_document(pdf_path, metadata={"subject": "Biology", "topic": "Photosynthesis"}, db_path=db_path)
    second = process_document(pdf_path, metadata={"subject": "Biology", "topic": "Photosynthesis"}, db_path=db_path)

    assert first["ok"] is True
    assert first["source_type"] == "pdf"
    assert second["cache_hit"] is True

    search = search_all(keyword="chlorophyll", db_path=db_path)
    assert search
    assert search[0]["present"] is True

    quiz = generate_quiz(question_count=20, db_path=db_path)
    assert len(quiz) == 20
    assert all(set(item["options"]) == {"A", "B", "C", "D"} for item in quiz)
    assert all(item["correct_answer"] in {"A", "B", "C", "D"} for item in quiz)

    revision = generate_revision_plan(db_path=db_path)
    assert revision["mind_map"]["topics"]
    assert "question_bank" in revision

    stats = get_dashboard_stats(db_path=db_path)
    assert stats["metrics"]["Uploaded PDFs"] == "1"
    assert stats["metrics"]["Quiz Generated"] == "1"
    assert stats["metrics"]["Revision Available"] == "Yes"


def test_non_pdf_inputs_are_disabled(tmp_path):
    db_path = tmp_path / "neuronote.db"
    reset_database(db_path)

    image_result = process_image({"name": "board.png", "content": b"image"}, db_path=db_path)
    audio_result = process_audio({"name": "lecture.wav", "content": b"audio"}, db_path=db_path)
    text_result = process_document({"name": "notes.txt", "content": "plain text"}, db_path=db_path)

    assert image_result["ok"] is False
    assert audio_result["ok"] is False
    assert text_result["ok"] is False
