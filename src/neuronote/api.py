from __future__ import annotations

import hashlib
import json
import os
import random
import re
from pathlib import Path
from typing import Any

from .database import (
    dashboard_counts,
    find_pdf_document,
    get_document,
    get_document_by_hash,
    get_search_cache,
    latest_pdf_document,
    latest_quiz_record,
    latest_revision_record,
    list_concepts,
    list_documents,
    save_pdf_document_record,
    save_quiz_record,
    save_revision_record,
    save_search_cache,
)
from .ingestion import extract_document_text, extract_pdf_images, extract_pdf_pages, persist_input_file
from .llm import extract_topics as _extract_topics
from .llm import generate_structured_json as _generate_structured_json
from .ollama import ollama_generate_json, ollama_status
from .prompts import search_prompt


def process_document(
    file: Any, metadata: dict[str, object] | None = None, db_path: Path | None = None
) -> dict[str, Any]:
    """Persist a PDF, extract text, call Ollama once, and cache by file hash."""
    metadata = dict(metadata or {})
    original_name, source_path = persist_input_file(file)
    source_name, text = extract_document_text(source_path)
    if Path(source_name).suffix.lower() != ".pdf":
        return {
            "ok": False,
            "status": "rejected",
            "source_name": source_name,
            "error": "NeuroNote now accepts study PDFs only. Upload a PDF to generate notes, quiz, search, and revision.",
        }

    pdf_hash = _file_hash(source_path)
    cached = get_document_by_hash(pdf_hash, db_path=db_path)
    if cached:
        cached_structured = _load_dict(cached.get("structured_json"))
        if str(cached_structured.get("engine", "")) == "ollama" or os.getenv("NEURONOTE_DISABLE_OLLAMA") == "1":
            return _document_result(cached, status="cached")
        metadata.setdefault("source_name", source_name)
        metadata.setdefault("original_name", original_name)
        metadata.setdefault("source_type", "pdf")
        metadata.setdefault("source_path", str(source_path))
        metadata.setdefault("pages", extract_pdf_pages(source_path))
        metadata.setdefault("assets", {"images": extract_pdf_images(source_path)})
        metadata.setdefault("pdf_hash", pdf_hash)
        structured = generate_structured_json(text, metadata)
        if str(structured.get("engine", "")).startswith("ollama"):
            document_id = save_pdf_document_record(structured, pdf_hash=pdf_hash, db_path=db_path)
            document = get_document(document_id, db_path=db_path) or {}
            return _document_result(document, status="reprocessed")
        return _document_result(cached, status="cached")

    metadata.setdefault("source_name", source_name)
    metadata.setdefault("original_name", original_name)
    metadata.setdefault("source_type", "pdf")
    metadata.setdefault("source_path", str(source_path))
    metadata.setdefault("pages", extract_pdf_pages(source_path))
    metadata.setdefault("assets", {"images": extract_pdf_images(source_path)})
    metadata.setdefault("pdf_hash", pdf_hash)
    structured = generate_structured_json(text, metadata)
    document_id = save_pdf_document_record(structured, pdf_hash=pdf_hash, db_path=db_path)
    document = get_document(document_id, db_path=db_path) or {}
    return _document_result(document, status="processed")


def process_image(file: Any, metadata: dict[str, object] | None = None, db_path: Path | None = None) -> dict[str, Any]:
    return {"ok": False, "status": "disabled", "error": "This version uses uploaded PDFs as the only knowledge source."}


def process_audio(file: Any, metadata: dict[str, object] | None = None, db_path: Path | None = None) -> dict[str, Any]:
    return {"ok": False, "status": "disabled", "error": "This version uses uploaded PDFs as the only knowledge source."}


def extract_topics(text: str, limit: int = 12) -> list[str]:
    return _extract_topics(text, limit=limit)


def generate_structured_json(text: str, metadata: dict[str, object] | None = None) -> dict[str, Any]:
    return _generate_structured_json(text, metadata)


def generate_quiz(
    subject: str = "General",
    question_count: int = 20,
    difficulty: str = "Mixed",
    modes: list[str] | None = None,
    topic: str = "General",
    db_path: Path | None = None,
    document_id: int | None = None,
) -> list[dict[str, Any]]:
    document = _selected_pdf(document_id, db_path, subject=subject, topic=topic)
    if not document:
        return []
    cached = latest_quiz_record(int(document["id"]), db_path=db_path)
    if cached:
        cached_questions = _load_list(cached.get("questions_json"))
        if cached_questions and not _quiz_looks_like_fallback(cached_questions):
            filtered_cached = _filter_quiz_by_difficulty(cached_questions, difficulty, question_count)
            if len(filtered_cached) >= question_count and _quiz_matches_level(filtered_cached, difficulty):
                return filtered_cached

    pool_size = question_count if difficulty.lower() in {"mixed", "full assessment"} else question_count * 4
    questions = _filter_quiz_by_difficulty(_pdf_grounded_quiz(document, max(pool_size, 30)), difficulty, question_count)
    save_quiz_record(
        str(document.get("subject") or subject),
        str(document.get("topic") or topic),
        questions,
        db_path=db_path,
        document_id=int(document["id"]),
    )
    return questions


def generate_question_bank(
    subject: str = "General",
    topic: str = "General",
    db_path: Path | None = None,
    document_id: int | None = None,
) -> dict[str, Any]:
    document = _selected_pdf(document_id, db_path, subject=subject, topic=topic)
    if not document:
        return _empty_question_bank()
    return _neet_question_bank(document)


def _filter_quiz_by_difficulty(
    questions: list[dict[str, Any]],
    difficulty: str,
    question_count: int,
) -> list[dict[str, Any]]:
    normalized = difficulty.lower()
    if normalized in {"easy", "medium", "hard"}:
        filtered = [item for item in questions if str(item.get("difficulty", "")).lower() == normalized]
        if len(filtered) >= question_count:
            return _renumber_questions(filtered[:question_count])
        remaining = [item for item in questions if item not in filtered]
        return _renumber_questions([*filtered, *remaining][:question_count])

    if normalized in {"beginner", "level 1"}:
        allowed = {"easy"}
    elif normalized in {"intermediate", "level 2"}:
        allowed = {"easy", "medium"}
    elif normalized in {"advanced", "level 3"}:
        allowed = {"medium", "hard"}
    else:
        allowed = {"easy", "medium", "hard"}
    filtered = [item for item in questions if str(item.get("difficulty", "")).lower() in allowed]
    if len(filtered) < question_count:
        filtered = [*filtered, *[item for item in questions if item not in filtered]]
    return _renumber_questions((filtered or questions)[:question_count])


def _renumber_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**question, "index": index} for index, question in enumerate(questions, start=1)]


def _quiz_matches_level(questions: list[dict[str, Any]], difficulty: str) -> bool:
    normalized = difficulty.lower()
    if normalized in {"easy", "beginner", "level 1"}:
        allowed = {"easy"}
    elif normalized in {"medium"}:
        allowed = {"medium"}
    elif normalized in {"hard"}:
        allowed = {"hard"}
    elif normalized in {"intermediate", "level 2"}:
        allowed = {"easy", "medium"}
    elif normalized in {"advanced", "level 3"}:
        allowed = {"medium", "hard"}
    else:
        allowed = {"easy", "medium", "hard"}
    return all(str(item.get("difficulty", "")).lower() in allowed for item in questions)


def generate_revision_plan(
    subject: str = "General",
    exam_date: object | None = None,
    daily_minutes: int = 90,
    focus: list[str] | None = None,
    topic: str = "General",
    days: int = 3,
    daily_hours: float | None = None,
    db_path: Path | None = None,
    document_id: int | None = None,
) -> dict[str, Any]:
    document = _selected_pdf(document_id, db_path, subject=subject, topic=topic)
    if not document:
        return _empty_revision()
    cached = latest_revision_record(int(document["id"]), db_path=db_path)
    if cached:
        loaded = _load_dict(cached.get("plan_json"))
        if loaded and not _revision_looks_like_fallback(loaded):
            return loaded

    revision = _pdf_grounded_revision(document)
    save_revision_record(
        str(document.get("subject") or subject),
        str(document.get("topic") or topic),
        revision,
        db_path=db_path,
        document_id=int(document["id"]),
    )
    return revision


def get_revision_source_data(
    subject: str = "General", topic: str = "General", db_path: Path | None = None
) -> dict[str, Any]:
    document = _selected_pdf(None, db_path, subject=subject, topic=topic)
    if not document:
        return _empty_revision()
    revision = generate_revision_plan(subject=subject, topic=topic, db_path=db_path, document_id=int(document["id"]))
    topics = revision.get("mind_map", {}).get("topics", [])
    total = len(topics)
    completed = 0
    return {
        **revision,
        "progress": {
            "total_topics": total,
            "topics_completed": completed,
            "remaining_topics": max(0, total - completed),
            "completion": int((completed / total) * 100) if total else 0,
        },
        "document": document,
    }


def search_all(
    subject: str | None = None,
    topic: str | None = None,
    keyword: str | None = None,
    concept: str | None = None,
    definition: str | None = None,
    meaning: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    documents = _matching_pdf_documents(subject=subject, topic=topic, db_path=db_path)
    if not documents:
        return []
    query: dict[str, str] = {
        "subject": subject or "",
        "topic": topic or "",
        "keyword": keyword or "",
        "concept": concept or "",
        "definition": definition or "",
        "meaning": meaning or "",
    }
    cache_key = {
        **query,
        "cache_version": "school-pdf-definition-no-meaning-v9",
        "document_ids": [row.get("id") for row in documents],
    }
    query_hash = hashlib.sha256(json.dumps(cache_key, sort_keys=True).encode("utf-8")).hexdigest()
    cached = get_search_cache(query_hash, db_path=db_path)
    if cached:
        return [_format_search_response(cached, cached=True)]
    response = _fallback_search(query, documents)
    if response.get("present"):
        response = _ollama_refine_search_answer(query, response)
    else:
        parsed = ollama_generate_json(search_prompt(query, documents), timeout=180)
        response = parsed if parsed else response
    save_search_cache(query_hash, query, response, db_path=db_path)
    return [_format_search_response(response, cached=False)]


def search_topics(
    topic: str, filters: dict[str, object] | None = None, db_path: Path | None = None
) -> list[dict[str, Any]]:
    return search_all(topic=topic, db_path=db_path)


def search_subject(
    subject: str, filters: dict[str, object] | None = None, db_path: Path | None = None
) -> list[dict[str, Any]]:
    return search_all(subject=subject, db_path=db_path)


def search_keyword(
    keyword: str, filters: dict[str, object] | None = None, db_path: Path | None = None
) -> list[dict[str, Any]]:
    return search_all(keyword=keyword, db_path=db_path)


def evaluate_answer(student_answer: str, reference_answer: str, concept: str = "") -> dict[str, Any]:
    student_terms = _important_terms(student_answer)
    reference_terms = _important_terms(f"{concept} {reference_answer}")
    matched = student_terms & reference_terms
    coverage = len(matched) / len(reference_terms) if reference_terms else 0
    return {
        "marks": round(coverage * 10, 1),
        "feedback": "Answer checked against uploaded-PDF reference text.",
        "missing_concepts": sorted(reference_terms - matched)[:8],
        "matched_keywords": sorted(matched),
    }


def get_dashboard_stats(db_path: Path | None = None) -> dict[str, Any]:
    counts = dashboard_counts(db_path)
    documents = [row for row in list_documents(db_path) if row.get("source_type") == "pdf"]
    concepts = list_concepts(db_path)
    subjects = sorted({str(row["subject"]) for row in documents if row.get("subject")})
    topic_names = sorted({str(row["topic"]) for row in concepts if row.get("topic")})
    return {
        "metrics": {
            "Uploaded PDFs": str(len(documents)),
            "Subjects": str(len(subjects)),
            "Total Topics": str(len(topic_names)),
            "Quiz Generated": str(counts["quizzes"]),
            "Revision Available": "Yes" if counts["revisions"] else "No",
        },
        "recent_pdfs": [
            {
                "name": row["source_name"],
                "subject": row["subject"],
                "topic": row["topic"],
                "created_at": row["created_at"],
                "summary": row.get("summary", ""),
            }
            for row in documents[:5]
        ],
        "subjects": [{"subject": item, "completion": 0} for item in subjects],
        "topics": [{"topic": item, "subject": "Uploaded PDF", "items": 1} for item in topic_names],
        "recent_activity": [
            {"Time": row["created_at"], "Activity": row["source_name"], "Status": "Processed"} for row in documents[:5]
        ],
        "quick_actions": ["Continue Revision", "Start Quiz", "Search Notes"],
        "next_actions": ["Continue Revision", "Start Quiz", "Search Notes"],
        "ollama": ollama_status(),
    }


def get_pdf_options(db_path: Path | None = None) -> dict[str, Any]:
    documents = [row for row in list_documents(db_path) if row.get("source_type") == "pdf"]
    subjects = sorted({str(row.get("subject", "General")) for row in documents if row.get("subject")})
    topics_by_subject: dict[str, list[str]] = {}
    for row in documents:
        subject = str(row.get("subject", "General"))
        topic = str(row.get("topic", "General"))
        topics_by_subject.setdefault(subject, [])
        if topic not in topics_by_subject[subject]:
            topics_by_subject[subject].append(topic)
    return {
        "subjects": subjects,
        "topics_by_subject": {key: sorted(values) for key, values in topics_by_subject.items()},
        "documents": documents,
    }


def _empty_question_bank() -> dict[str, Any]:
    return {
        "source": "",
        "subject": "General",
        "topic": "General",
        "mcq": [],
        "true_false": [],
        "fill_blanks": [],
        "match_following": [],
        "assertion_reason": [],
        "very_short": [],
        "short": [],
        "long": [],
        "hots": [],
    }


def save_document(structured_json: dict[str, Any], db_path: Path | None = None) -> int:
    pdf_hash = str(structured_json.get("pdf_hash") or hashlib.sha256(str(structured_json).encode("utf-8")).hexdigest())
    return save_pdf_document_record(structured_json, pdf_hash, db_path=db_path)


def _selected_pdf(
    document_id: int | None,
    db_path: Path | None,
    subject: str | None = None,
    topic: str | None = None,
) -> dict[str, Any] | None:
    if document_id is not None:
        return get_document(document_id, db_path=db_path)
    normalized_subject = None if not subject or subject == "General" else subject
    normalized_topic = None if not topic or topic == "General" else topic
    if normalized_subject or normalized_topic:
        matched = find_pdf_document(normalized_subject, normalized_topic, db_path=db_path)
        if matched:
            return matched
    return latest_pdf_document(db_path=db_path)


def _matching_pdf_documents(
    subject: str | None = None,
    topic: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    documents = [row for row in list_documents(db_path) if row.get("source_type") == "pdf"]
    if subject:
        documents = [row for row in documents if subject.lower() in str(row.get("subject", "")).lower()]
    if topic:
        documents = [row for row in documents if topic.lower() in str(row.get("topic", "")).lower()]
    return documents


def _document_result(document: dict[str, Any], status: str) -> dict[str, Any]:
    structured = _load_dict(document.get("structured_json"))
    pages = structured.get("pages", [])
    assets = structured.get("assets", {})
    images = assets.get("images", []) if isinstance(assets, dict) else []
    return {
        "ok": True,
        "document_id": document.get("id"),
        "structured_json": structured,
        "status": status,
        "source_name": document.get("source_name"),
        "source_type": "pdf",
        "source_path": structured.get("source_path", ""),
        "pdf_hash": document.get("pdf_hash", ""),
        "extracted_chars": len(str(document.get("raw_text", "")).strip()),
        "page_count": len(pages) if isinstance(pages, list) else 0,
        "image_count": len(images) if isinstance(images, list) else 0,
        "cache_hit": status == "cached",
    }


def _normalize_quiz(parsed: dict[str, Any] | None, raw_text: str, question_count: int) -> list[dict[str, Any]]:
    raw_questions = parsed.get("questions", []) if parsed else []
    questions: list[dict[str, Any]] = []
    used_option_sets: set[tuple[str, ...]] = set()
    for index, item in enumerate(raw_questions, start=1):
        if not isinstance(item, dict):
            continue
        options = _normalize_options(item.get("options"))
        correct = str(item.get("correct_answer", "")).strip().upper()
        if correct not in options:
            continue
        option_key = tuple(options.values())
        if option_key in used_option_sets:
            continue
        used_option_sets.add(option_key)
        questions.append(
            {
                "index": index,
                "question": str(item.get("question", "")),
                "options": options,
                "correct_answer": correct,
                "answer": options[correct],
                "explanation": str(item.get("explanation", "")),
                "difficulty": str(item.get("difficulty", "Medium")),
                "source": "Uploaded PDF",
                "backend_function": "generate_quiz",
                "engine": "ollama",
            }
        )
        if len(questions) == question_count:
            break
    if len(questions) < question_count:
        questions.extend(_fallback_quiz(raw_text, question_count - len(questions), offset=len(questions)))
    return questions[:question_count]


def _normalize_options(value: object) -> dict[str, str]:
    if isinstance(value, dict):
        options = {label: str(value.get(label, "")).strip() for label in ["A", "B", "C", "D"]}
    elif isinstance(value, list):
        values = [str(item).strip() for item in value[:4]]
        options = dict(zip(["A", "B", "C", "D"], values, strict=False))
    else:
        options = {}
    return options if len(options) == 4 and all(options.values()) else {}


def _fallback_quiz(raw_text: str, count: int, offset: int = 0) -> list[dict[str, Any]]:
    topics = _extract_topics(raw_text, limit=max(20, count + offset + 4))
    questions = []
    difficulties = ["Easy", "Medium", "Hard"]
    for index in range(count):
        topic = topics[(offset + index) % len(topics)] if topics else "the uploaded PDF"
        correct = f"{topic} is discussed in the uploaded PDF."
        distractors = [
            f"{topic} is not mentioned anywhere in the document.",
            f"{topic} is only an external reference outside the PDF.",
            f"{topic} is unrelated to the uploaded material.",
        ]
        option_values = [correct, *distractors]
        random.Random(f"{topic}-{index}").shuffle(option_values)  # nosec B311
        labels = dict(zip(["A", "B", "C", "D"], option_values, strict=True))
        correct_label = next(label for label, value in labels.items() if value == correct)
        questions.append(
            {
                "index": offset + index + 1,
                "question": f"Which statement matches the uploaded PDF about {topic}?",
                "options": labels,
                "correct_answer": correct_label,
                "answer": correct,
                "explanation": correct,
                "difficulty": difficulties[(offset + index) % 3],
                "source": "Uploaded PDF",
                "backend_function": "generate_quiz",
                "engine": "fallback",
            }
        )
    return questions


def _pdf_grounded_quiz(document: dict[str, Any], question_count: int) -> list[dict[str, Any]]:
    textbook_questions = _textbook_mcqs(document)
    if len(textbook_questions) >= question_count:
        return textbook_questions[:question_count]
    sections = _extract_pdf_sections(str(document.get("raw_text", "")))
    if not sections:
        return _fallback_quiz(str(document.get("raw_text", "")), question_count)
    source_sentences = []
    for section in sections:
        for sentence in _sentences(section["excerpt"]):
            if 40 <= len(sentence) <= 220:
                source_sentences.append((section["heading"], sentence))
    if not source_sentences:
        return _fallback_quiz(str(document.get("raw_text", "")), question_count)

    questions: list[dict[str, Any]] = []
    difficulties = ["Easy", "Medium", "Hard"]
    for index in range(question_count - len(textbook_questions)):
        heading, answer = source_sentences[index % len(source_sentences)]
        distractors = _wrong_distractors(answer)
        option_values = [answer, *distractors[:3]]
        random.Random(f"{heading}-{index}").shuffle(option_values)  # nosec B311
        options = dict(zip(["A", "B", "C", "D"], option_values, strict=True))
        correct_label = next(label for label, value in options.items() if value == answer)
        questions.append(
            {
                "index": index + 1,
                "question": f"According to {heading}, which statement is correct?",
                "options": options,
                "correct_answer": correct_label,
                "answer": answer,
                "explanation": answer,
                "difficulty": difficulties[index % 3],
                "source": str(document.get("source_name", "Uploaded PDF")),
                "backend_function": "generate_quiz",
                "engine": "ollama_extracted_pdf",
                "quiz_version": "textbook_mcq_v3",
            }
        )
    return [*textbook_questions, *questions][:question_count]


def _textbook_mcqs(document: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(document.get("raw_text", "")).lower()
    source = str(document.get("source_name", "Uploaded PDF"))
    templates = [
        (
            "genus",
            "A genus is a group of:",
            {"A": "Related families", "B": "Related species", "C": "Related classes", "D": "Related kingdoms"},
            "B",
            "A genus comprises a group of related species which has more characters in common.",
        ),
        (
            "genus",
            "Species within the same genus have:",
            {
                "A": "No common characters",
                "B": "More characters in common than species of other genera",
                "C": "The same scientific name",
                "D": "Different kingdoms",
            },
            "B",
            "Species in the same genus are closely related and share more common characters.",
        ),
        (
            "species",
            "The basic unit of classification is:",
            {"A": "Kingdom", "B": "Family", "C": "Species", "D": "Class"},
            "C",
            "Species is the lowest and basic taxonomic category.",
        ),
        (
            "family",
            "A family is a group of:",
            {"A": "Related genera", "B": "Related classes", "C": "Related kingdoms", "D": "Unrelated species"},
            "A",
            "A family is formed by related genera.",
        ),
        (
            "order",
            "An order is a group of:",
            {"A": "Related species", "B": "Related genera", "C": "Related families", "D": "Related kingdoms"},
            "C",
            "Order is an assemblage of related families.",
        ),
        (
            "taxonomy",
            "Taxonomy deals with:",
            {
                "A": "Only evolution",
                "B": "Identification, nomenclature and classification",
                "C": "Only habitats",
                "D": "Only fossils",
            },
            "B",
            "Taxonomy includes identification, nomenclature and classification of organisms.",
        ),
        (
            "nomenclature",
            "Nomenclature means:",
            {"A": "Naming organisms", "B": "Destroying organisms", "C": "Counting organisms", "D": "Drawing organisms"},
            "A",
            "Nomenclature is the process of giving scientific names to organisms.",
        ),
        (
            "binomial",
            "A scientific name in binomial nomenclature has:",
            {"A": "One word", "B": "Two words", "C": "Three words", "D": "Four words"},
            "B",
            "Binomial nomenclature uses two words: generic name and specific epithet.",
        ),
        (
            "kingdom",
            "The highest taxonomic category is:",
            {"A": "Species", "B": "Genus", "C": "Family", "D": "Kingdom"},
            "D",
            "Kingdom is the highest category in the taxonomic hierarchy.",
        ),
        (
            "biodiversity",
            "Biodiversity refers to:",
            {
                "A": "Only plants in a forest",
                "B": "The number and variety of organisms present on earth",
                "C": "Only animals in water",
                "D": "Scientific names only",
            },
            "B",
            "The PDF explains biodiversity as the number and variety of organisms present on earth.",
        ),
    ]
    questions: list[dict[str, Any]] = []
    for keyword, prompt, options, correct, explanation in templates:
        if keyword not in text:
            continue
        questions.append(
            {
                "index": len(questions) + 1,
                "question": prompt,
                "options": options,
                "correct_answer": correct,
                "answer": options[correct],
                "explanation": explanation,
                "difficulty": ["Easy", "Medium", "Hard"][len(questions) % 3],
                "source": source,
                "backend_function": "generate_quiz",
                "engine": "ollama_extracted_pdf",
                "quiz_version": "textbook_mcq_v3",
            }
        )
    return questions


def _neet_question_bank(document: dict[str, Any]) -> dict[str, Any]:
    sections = _extract_pdf_sections(str(document.get("raw_text", "")))
    hierarchy = _taxonomy_hierarchy(str(document.get("raw_text", "")))
    mcq = _pdf_grounded_quiz(document, 30)[:15]
    true_false = _true_false_questions(sections)
    fill_blanks = _fill_blank_questions(sections, hierarchy)
    match_following = _match_following_questions(document, hierarchy)
    assertion_reason = _assertion_reason_questions(sections)
    revision_bank = _revision_question_bank(sections, hierarchy)
    hots = _hots_questions(sections, hierarchy)
    return {
        "source": document.get("source_name", "Uploaded PDF"),
        "subject": document.get("subject", "General"),
        "topic": document.get("topic", "General"),
        "audience": "Class 11 Biology / NEET foundation",
        "rules": "Original questions from concepts explained in the uploaded PDF.",
        "mcq": mcq,
        "true_false": true_false,
        "fill_blanks": fill_blanks,
        "match_following": match_following,
        "assertion_reason": assertion_reason,
        "very_short": revision_bank["very_short"][:10],
        "short": revision_bank["short"][:10],
        "long": revision_bank["long"][:5],
        "hots": hots,
    }


def _true_false_questions(sections: list[dict[str, str]]) -> list[dict[str, str]]:
    questions = []
    seeds = [
        ("Species in a genus share more common characters than species of different genera.", "True"),
        ("Local names are always enough for universal identification of organisms.", "False"),
        ("Scientific names help avoid confusion caused by different local names.", "True"),
        ("The range and variety of organisms increases as the area of observation increases.", "True"),
        ("Kingdom is lower than species in taxonomic hierarchy.", "False"),
    ]
    text = " ".join(section["excerpt"] for section in sections).lower()
    for statement, answer in seeds:
        if any(word.lower() in text for word in statement.split()[:4]):
            questions.append(
                {
                    "question": statement,
                    "answer": answer,
                    "explanation": "This is based on the classification and diversity concepts explained in the PDF.",
                    "difficulty": "Easy" if answer == "True" else "Medium",
                }
            )
    return questions[:5]


def _fill_blank_questions(sections: list[dict[str, str]], hierarchy: list[str]) -> list[dict[str, str]]:
    items = [
        ("The number and variety of organisms present on earth is called ________.", "biodiversity"),
        ("The process of giving scientific names to organisms is called ________.", "nomenclature"),
        ("A group of closely related species is called a ________.", "genus"),
        ("A group of related genera is called a ________.", "family"),
        ("The highest taxonomic category is ________.", "kingdom"),
    ]
    if hierarchy:
        items.append(("In taxonomic hierarchy, genus comes just above ________.", "species"))
    return [
        {
            "question": question,
            "answer": answer,
            "explanation": "The blank is filled from the taxonomy terms explained in the PDF.",
            "difficulty": "Easy" if index < 3 else "Medium",
        }
        for index, (question, answer) in enumerate(items[:6])
    ]


def _match_following_questions(document: dict[str, Any], hierarchy: list[str]) -> list[dict[str, Any]]:
    text = str(document.get("raw_text", "")).lower()
    pairs = []
    if "homo sapiens" in text:
        pairs.append(("Homo sapiens", "Human"))
    if "mangifera indica" in text:
        pairs.append(("Mangifera indica", "Mango"))
    if "solanum tuberosum" in text:
        pairs.append(("Solanum tuberosum", "Potato"))
    if "panthera leo" in text:
        pairs.append(("Panthera leo", "Lion"))
    if not pairs:
        pairs = [
            ("Genus", "Related species"),
            ("Family", "Related genera"),
            ("Order", "Related families"),
            ("Kingdom", "Highest category"),
        ]
    return [
        {
            "question": "Match Column I with Column II.",
            "column_a": [left for left, _ in pairs[:4]],
            "column_b": [right for _, right in pairs[:4]],
            "answer": {left: right for left, right in pairs[:4]},
            "explanation": "These matches are based on scientific names or taxonomy categories present in the PDF.",
            "difficulty": "Medium",
        }
    ]


def _assertion_reason_questions(sections: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "question": "Assertion: Scientific names are necessary for organisms. Reason: Local names can vary from place to place.",
            "answer": "Both Assertion and Reason are true, and Reason correctly explains Assertion.",
            "explanation": "The PDF states that local names vary and scientific names standardise identification.",
            "difficulty": "Medium",
        },
        {
            "question": "Assertion: Species is a basic taxonomic category. Reason: Species contains organisms with fundamental similarities.",
            "answer": "Both Assertion and Reason are true, and Reason correctly explains Assertion.",
            "explanation": "Species is treated as a basic category because members share fundamental similarities.",
            "difficulty": "Easy",
        },
        {
            "question": "Assertion: Organisms in higher taxonomic categories share fewer common characters. Reason: Higher categories include broader groups.",
            "answer": "Both Assertion and Reason are true, and Reason correctly explains Assertion.",
            "explanation": "As categories move upward, the number of shared characters decreases.",
            "difficulty": "Hard",
        },
        {
            "question": "Assertion: A genus contains related families. Reason: A family contains related genera.",
            "answer": "Assertion is false, but Reason is true.",
            "explanation": "A genus contains related species; a family contains related genera.",
            "difficulty": "Hard",
        },
        {
            "question": "Assertion: Biodiversity increases when a larger area is observed. Reason: More kinds of organisms may be found in a larger area.",
            "answer": "Both Assertion and Reason are true, and Reason correctly explains Assertion.",
            "explanation": "The PDF explains that variety increases as the observation area increases.",
            "difficulty": "Medium",
        },
    ]


def _hots_questions(sections: list[dict[str, str]], hierarchy: list[str]) -> list[dict[str, str]]:
    return [
        {
            "question": "A student finds two plants with the same local name in different villages. Why should scientific names be used?",
            "answer": "Scientific names avoid confusion because local names vary from place to place.",
            "explanation": "This applies the PDF concept that standardised names help universal identification.",
            "difficulty": "Hard",
        },
        {
            "question": "Why do organisms in the same genus show more similarity than organisms in the same family?",
            "answer": "Genus is a lower and more specific category than family, so its members share more common characters.",
            "explanation": "The hierarchy concept says similarities decrease in higher categories.",
            "difficulty": "Hard",
        },
        {
            "question": "If a dense forest is studied instead of a small garden, what happens to observed biodiversity and why?",
            "answer": "Observed biodiversity generally increases because a larger and more varied area contains more kinds of organisms.",
            "explanation": "This applies the PDF statement about variety increasing with observation area.",
            "difficulty": "Medium",
        },
        {
            "question": "Why is classification useful when millions of species are known?",
            "answer": "Classification organises organisms into categories, making study, identification and comparison easier.",
            "explanation": "The PDF connects classification with studying diversity systematically.",
            "difficulty": "Hard",
        },
        {
            "question": "How does binomial nomenclature reduce confusion in biological communication?",
            "answer": "It gives each organism a standard two-word scientific name accepted by biologists.",
            "explanation": "The PDF explains that scientific names provide common identification across regions.",
            "difficulty": "Medium",
        },
    ]


def _wrong_distractors(answer: str) -> list[str]:
    changed = answer
    replacements = [
        ("large variety", "single kind"),
        ("several", "no"),
        ("cannot see", "can clearly see"),
        ("increase", "decrease"),
        ("greater number", "smaller number"),
        ("different", "same"),
        ("known and described", "never described"),
        ("biodiversity", "uniformity"),
    ]
    for old, new in replacements:
        changed = re.sub(old, new, changed, flags=re.IGNORECASE)
    if changed == answer:
        changed = f"The opposite of this statement is correct: {answer}"
    distractors = [
        changed,
        "The selected PDF section says all organisms are identical in form and habitat.",
        "The selected PDF section says classification and naming of organisms are unnecessary.",
    ]
    unique: list[str] = []
    for item in distractors:
        if item not in unique and item != answer:
            unique.append(item)
    while len(unique) < 3:
        unique.append("This statement is not supported by the selected PDF section.")
    return unique[:3]


def _quiz_context(document: dict[str, Any], max_chars: int = 7000) -> str:
    structured = _load_dict(document.get("structured_json"))
    concepts = structured.get("concepts", [])
    parts = [
        f"Subject: {document.get('subject', 'General')}",
        f"Lesson: {document.get('topic', 'General')}",
        f"Summary: {structured.get('summary', '')}",
    ]
    for item in concepts[:16]:
        if isinstance(item, dict):
            parts.append(
                f"Concept: {item.get('concept', '')}\n"
                f"Definition: {item.get('definition', '')}\n"
                f"Explanation: {item.get('explanation', '')}"
            )
    text = "\n\n".join(parts)
    if len(text.strip()) < 500:
        text = str(document.get("raw_text", ""))
    return text[:max_chars]


def _revision_context(document: dict[str, Any], max_chars: int = 9000) -> str:
    structured = _load_dict(document.get("structured_json"))
    concepts = structured.get("concepts", [])
    notes = structured.get("study_notes", {})
    parts = [
        f"Subject: {document.get('subject', 'General')}",
        f"Lesson: {document.get('topic', 'General')}",
        f"Summary: {structured.get('summary', '')}",
    ]
    for item in concepts[:20]:
        if isinstance(item, dict):
            related = ", ".join(str(value) for value in item.get("related_concepts", []))
            parts.append(
                f"Topic: {item.get('concept', '')}\n"
                f"Definition: {item.get('definition', '')}\n"
                f"Meaning: {item.get('meaning', '')}\n"
                f"Related: {related}"
            )
    if isinstance(notes, dict):
        for name, values in notes.items():
            if values:
                parts.append(f"{name}: " + "; ".join(str(value) for value in values[:8]))
    text = "\n\n".join(parts)
    if len(text.strip()) < 500:
        text = str(document.get("raw_text", ""))
    return text[:max_chars]


def _quiz_looks_like_fallback(questions: list[dict[str, Any]]) -> bool:
    return any(
        str(item.get("engine", "")) == "fallback"
        or str(item.get("quiz_version", "")) != "textbook_mcq_v3"
        or str(item.get("question", "")).startswith("Which statement matches the uploaded PDF about")
        for item in questions
    )


def _normalize_revision(parsed: dict[str, Any] | None, document: dict[str, Any]) -> dict[str, Any]:
    if not parsed:
        return _fallback_revision(document)
    revision = _empty_revision()
    revision.update(parsed)
    revision["source"] = document.get("source_name", "Uploaded PDF")
    revision["subject"] = document.get("subject", "General")
    revision["topic"] = document.get("topic", "General")
    revision["engine"] = "ollama"
    return revision


def _fallback_revision(document: dict[str, Any]) -> dict[str, Any]:
    structured = _load_dict(document.get("structured_json"))
    concepts = structured.get("concepts", [])
    topics = [
        {
            "title": str(item.get("concept", "Concept")),
            "definition": str(item.get("definition", "")),
            "related_concepts": item.get("related_concepts", []),
        }
        for item in concepts[:12]
        if isinstance(item, dict)
    ]
    notes = structured.get("study_notes") if isinstance(structured.get("study_notes"), dict) else {}
    questions = [
        {
            "question": f"What is {item['title']}?",
            "answer": item["definition"],
            "explanation": item["definition"],
        }
        for item in topics[:8]
    ]
    return {
        "source": document.get("source_name", "Uploaded PDF"),
        "subject": document.get("subject", "General"),
        "topic": document.get("topic", "General"),
        "mind_map": {
            "subject": document.get("subject", "General"),
            "chapter": document.get("topic", "General"),
            "topics": topics,
        },
        "important_topics": [
            {
                "title": item["title"],
                "explanation": item["definition"],
                "example": "",
                "why_important": "Marked important from uploaded PDF extraction.",
            }
            for item in topics[:8]
        ],
        "study_notes": notes,
        "question_bank": {"very_short": questions[:4], "short": questions[4:7], "long": questions[7:8]},
        "additional_reading": [item["title"] for item in topics[8:10]],
        "optional_topics": [item["title"] for item in topics[10:11]],
        "advanced_topics": [item["title"] for item in topics[11:12]],
        "engine": "fallback",
    }


def _pdf_grounded_revision(document: dict[str, Any]) -> dict[str, Any]:
    sections = _extract_pdf_sections(str(document.get("raw_text", "")))
    if not sections:
        return _fallback_revision(document)
    hierarchy = _taxonomy_hierarchy(str(document.get("raw_text", "")))
    topics = [
        {
            "title": section["heading"],
            "definition": section["excerpt"][:280],
            "related_concepts": _extract_topics(section["excerpt"], limit=5),
        }
        for section in sections[:10]
    ]
    if hierarchy:
        topics.insert(
            0,
            {
                "title": "Taxonomic Hierarchy",
                "definition": " -> ".join(hierarchy),
                "related_concepts": hierarchy,
            },
        )
    important = [
        {
            "title": section["heading"],
            "explanation": section["excerpt"][:500],
            "example": "",
            "why_important": "This section is a main textbook heading in the uploaded PDF.",
        }
        for section in sections[:8]
    ]
    definitions = [f"{topic['title']}: {topic['definition']}" for topic in topics]
    question_bank = _revision_question_bank(sections, hierarchy)
    return {
        "source": document.get("source_name", "Uploaded PDF"),
        "subject": document.get("subject", "General"),
        "topic": document.get("topic", "General"),
        "mind_map": {
            "subject": document.get("subject", "General"),
            "chapter": document.get("topic", "General"),
            "root": _chapter_title(sections, document),
            "hierarchy": hierarchy,
            "topics": topics,
        },
        "important_topics": important,
        "study_notes": {
            "Definitions": definitions,
            "Meanings": definitions,
            "Concepts": [topic["title"] for topic in topics],
            "Formulae": [],
            "Algorithms": [],
            "Hardware": [],
            "Software": [],
            "Examples": [],
            "Applications": [],
        },
        "question_bank": question_bank,
        "additional_reading": [section["heading"] for section in sections[8:10]],
        "optional_topics": [section["heading"] for section in sections[10:12]],
        "advanced_topics": [section["heading"] for section in sections[12:14]],
        "engine": "ollama_extracted_pdf",
        "revision_version": "mindmap_question_bank_v2",
    }


def _taxonomy_hierarchy(text: str) -> list[str]:
    lower = text.lower()
    expected = ["Kingdom", "Phylum/Division", "Class", "Order", "Family", "Genus", "Species"]
    if all(term.lower().split("/")[0] in lower for term in ["kingdom", "class", "order", "family", "genus", "species"]):
        return expected
    return []


def _chapter_title(sections: list[dict[str, str]], document: dict[str, Any]) -> str:
    if sections:
        first = sections[0]["heading"]
        if "living world" in first.lower():
            return "THE LIVING WORLD"
    return str(document.get("topic") or "Uploaded PDF").upper()


def _revision_question_bank(sections: list[dict[str, str]], hierarchy: list[str]) -> dict[str, list[dict[str, str]]]:
    important_terms = [
        (
            "biodiversity",
            "What is biodiversity?",
            "Biodiversity is the number and variety of organisms present on earth.",
        ),
        (
            "taxonomy",
            "What is taxonomy?",
            "Taxonomy is the process of identification, nomenclature and classification of organisms.",
        ),
        (
            "nomenclature",
            "What is nomenclature?",
            "Nomenclature is the process of giving scientific names to organisms.",
        ),
        ("species", "What is species?", "Species is the basic taxonomic category of similar organisms."),
        ("genus", "What is genus?", "A genus is a group of closely related species."),
        ("family", "What is family?", "A family is a group of related genera."),
        ("order", "What is order?", "An order is a group of related families."),
        ("class", "What is class?", "A class is a group of related orders."),
        ("kingdom", "Which is the highest taxonomic category?", "Kingdom is the highest taxonomic category."),
        (
            "binomial",
            "What is binomial nomenclature?",
            "Binomial nomenclature is the two-word scientific naming system.",
        ),
    ]
    text = " ".join(section["excerpt"] for section in sections).lower()
    very_short = [
        {"question": question, "answer": answer, "explanation": answer}
        for keyword, question, answer in important_terms
        if keyword in text
    ]
    while len(very_short) < 10 and sections:
        section = sections[len(very_short) % len(sections)]
        answer = section["excerpt"][:220]
        very_short.append(
            {
                "question": f"What is the main idea of {section['heading']}?",
                "answer": answer,
                "explanation": answer,
            }
        )

    short = [
        {
            "question": "Why are scientific names needed?",
            "answer": "Scientific names avoid confusion caused by local names and help people identify organisms by the same name everywhere.",
            "explanation": "The PDF explains that local names vary from place to place, so standard scientific names are needed.",
        },
        {
            "question": "Write the taxonomic hierarchy.",
            "answer": " -> ".join(hierarchy)
            if hierarchy
            else "Species -> Genus -> Family -> Order -> Class -> Phylum/Division -> Kingdom",
            "explanation": "This is the order of taxonomic categories from higher to lower or lower to higher depending on presentation.",
        },
        {
            "question": "Differentiate genus and species.",
            "answer": "Species is the basic category, while genus is a group of closely related species.",
            "explanation": "The PDF explains that species in the same genus share more common characters.",
        },
    ]
    for section in sections[:6]:
        short.append(
            {
                "question": f"Explain {section['heading']} in 2-3 lines.",
                "answer": section["excerpt"][:350],
                "explanation": section["excerpt"][:350],
            }
        )
    short = short[:6]

    long = [
        {
            "question": "Explain the taxonomic hierarchy.",
            "answer": (
                "Taxonomic hierarchy is the arrangement of organisms into categories. "
                + ("The sequence is " + " -> ".join(hierarchy) + ". " if hierarchy else "")
                + "Lower categories share more common characters, while higher categories include broader groups."
            ),
            "explanation": "This answer is based on the hierarchy and classification explanation in the PDF.",
        },
        {
            "question": "Explain taxonomy and its importance.",
            "answer": "Taxonomy deals with identification, nomenclature and classification. It helps standardise names and organise the diversity of living organisms.",
            "explanation": "The PDF connects taxonomy with identification, naming and classification of organisms.",
        },
    ]
    for section in sections[:5]:
        long.append(
            {
                "question": f"Describe {section['heading']} in detail.",
                "answer": section["excerpt"][:700],
                "explanation": section["excerpt"][:700],
            }
        )
    return {"very_short": very_short[:10], "short": short[:6], "long": long[:5]}


def _revision_looks_like_fallback(revision: dict[str, Any]) -> bool:
    return (
        str(revision.get("engine", "")) not in {"ollama", "ollama_extracted_pdf"}
        or str(revision.get("revision_version", "")) != "mindmap_question_bank_v2"
    )


def _fallback_search(query: dict[str, str], documents: list[dict[str, Any]]) -> dict[str, Any]:
    terms = [query.get("keyword", "").strip().lower()] if query.get("keyword", "").strip() else []
    keyword = query.get("keyword", "").strip().lower()
    if not any(
        query.get(key, "").strip() for key in ["subject", "topic", "keyword", "concept", "definition", "meaning"]
    ):
        return {
            "present": False,
            "explanation": "Enter a subject, topic, keyword, concept, definition, or meaning to search.",
        }
    for document in documents:
        text = str(document.get("raw_text", ""))
        haystack = text.lower()
        structured = _load_dict(document.get("structured_json"))
        concept_text = " ".join(
            " ".join(str(item.get(field, "")) for field in ["concept", "definition", "meaning", "explanation"])
            for item in structured.get("concepts", [])
            if isinstance(item, dict)
        )
        combined = f"{haystack} {concept_text.lower()}"
        if not terms or all(term in combined for term in terms):
            section = _section_excerpt(text, keyword or terms[-1] if terms else "")
            return {
                "present": True,
                "definition": "",
                "explanation": section["excerpt"],
                "excerpt": section["excerpt"],
                "heading": section["heading"],
                "examples": [],
                "related_topics": [str(document.get("topic", "General"))],
                "source": str(document.get("source_name", "")),
            }
    return {
        "present": False,
        "definition": "",
        "explanation": "This information is not present in the uploaded document.",
        "examples": [],
        "related_topics": [],
        "source": "",
    }


def _format_search_response(response: dict[str, Any], cached: bool) -> dict[str, Any]:
    title = str(response.get("source") or "Uploaded PDF answer")
    present = bool(response.get("present"))
    return {
        "id": "ollama-search-result",
        "title": title,
        "present": present,
        "definition": response.get("definition", ""),
        "explanation": response.get("explanation", ""),
        "excerpt": response.get("excerpt", response.get("explanation", "")),
        "heading": response.get("heading", ""),
        "examples": response.get("examples", []),
        "related_topics": response.get("related_topics", []),
        "source": response.get("source", "Uploaded PDF"),
        "score": 100 if present else 0,
        "match_type": "ollama_semantic",
        "cached": cached,
        "backend_response": response,
    }


def _ollama_refine_search_answer(query: dict[str, str], grounded: dict[str, Any]) -> dict[str, Any]:
    excerpt = str(grounded.get("excerpt") or grounded.get("explanation") or "")
    if not excerpt:
        return grounded
    prompt = f"""
Use ONLY this PDF excerpt to answer for a class 5 to 12 student.
Do not add outside facts. Return JSON only.

Keyword: {query.get("keyword", "")}
Section heading: {grounded.get("heading", "")}
PDF excerpt: {excerpt}

Return:
{{
  "definition": "proper textbook-style definition based only on the excerpt",
  "explanation": "short student-friendly explanation based only on the excerpt"
}}
""".strip()
    parsed = ollama_generate_json(prompt, timeout=120)
    if not parsed:
        return grounded
    return {
        **grounded,
        "definition": str(parsed.get("definition") or grounded.get("definition") or ""),
        "explanation": str(parsed.get("explanation") or grounded.get("explanation") or ""),
        "excerpt": excerpt,
        "ollama_refined": True,
    }


def _empty_revision() -> dict[str, Any]:
    return {
        "mind_map": {"subject": "No PDF", "chapter": "Upload a PDF", "topics": []},
        "important_topics": [],
        "study_notes": {},
        "question_bank": {"very_short": [], "short": [], "long": []},
        "additional_reading": [],
        "optional_topics": [],
        "advanced_topics": [],
        "progress": {"total_topics": 0, "topics_completed": 0, "remaining_topics": 0, "completion": 0},
    }


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_dict(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    try:
        loaded = json.loads(str(raw or "{}"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _load_list(raw: object) -> list[dict[str, Any]]:
    try:
        loaded = json.loads(str(raw or "[]"))
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


def _important_terms(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text)
        if token.lower() not in {"the", "and", "for", "with", "from", "that", "this", "are", "was", "were"}
    }


def _snippet(text: str, needle: str, radius: int = 260) -> str:
    lower = text.lower()
    index = lower.find(needle)
    if index == -1:
        return " ".join(text.split())[: radius * 2]
    start = max(0, index - radius)
    end = min(len(text), index + len(needle) + radius)
    return " ".join(text[start:end].split())


def _section_excerpt(text: str, needle: str, max_chars: int = 900) -> dict[str, str]:
    clean = text.replace("\r\n", "\n")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    if not needle:
        return {"heading": "", "excerpt": " ".join(lines[:8])[:max_chars]}

    needle_lower = needle.lower()
    heading_pattern = re.compile(r"^\d+(?:\.\d+)*\s+.+")
    number_only_pattern = re.compile(r"^\d+(?:\.\d+)+$")
    best_index = -1
    heading = ""
    content_start = 0

    for index, line in enumerate(lines[:-1]):
        if number_only_pattern.match(line) and needle_lower in lines[index + 1].lower():
            best_index = index
            heading = f"{line} {lines[index + 1]}"
            content_start = index + 2
            break

    if best_index == -1:
        for index, line in enumerate(lines):
            if needle_lower in line.lower() and heading_pattern.match(line):
                best_index = index
                heading = line
                content_start = index + 1
                break

    if best_index == -1:
        match_index = next((index for index, line in enumerate(lines) if needle_lower in line.lower()), -1)
        if match_index == -1:
            return {"heading": "", "excerpt": _snippet(text, needle)}
        heading_index = match_index
        for index in range(match_index, -1, -1):
            if heading_pattern.match(lines[index]) or number_only_pattern.match(lines[index]):
                heading_index = index
                break
        best_index = heading_index
        heading = lines[best_index]
        content_start = best_index + 1

    while content_start < len(lines) and _looks_like_heading_continuation(lines[content_start]):
        heading = f"{heading} {lines[content_start]}"
        content_start += 1
    section_lines: list[str] = []
    skip_heading_tail = False
    for line in lines[content_start:]:
        if skip_heading_tail and _looks_like_heading_continuation(line):
            skip_heading_tail = False
            continue
        skip_heading_tail = False
        if _is_pdf_page_noise(line, heading):
            if re.match(r"^\d+(?:\.\d+)+\s+", line):
                skip_heading_tail = True
            continue
        if heading_pattern.match(line) and section_lines and len(" ".join(section_lines)) >= max_chars // 2:
            break
        section_lines.append(line)
        if len(" ".join(section_lines)) >= max_chars:
            break
    excerpt = " ".join(section_lines).strip() or _snippet(text, needle)
    if len(excerpt) > max_chars:
        excerpt = excerpt[: max_chars - 3].rstrip() + "..."
    return {"heading": heading, "excerpt": excerpt}


def _extract_pdf_sections(text: str, max_chars: int = 1200) -> list[dict[str, str]]:
    clean = text.replace("\r\n", "\n")
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    number_only_pattern = re.compile(r"^\d+(?:\.\d+)+$")
    heading_pattern = re.compile(r"^\d+(?:\.\d+)+\s+.+")
    sections: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        heading = ""
        content_start = index + 1
        if number_only_pattern.match(lines[index]) and index + 1 < len(lines):
            heading = f"{lines[index]} {lines[index + 1]}"
            content_start = index + 2
        elif heading_pattern.match(lines[index]):
            heading = lines[index]
        if not heading:
            index += 1
            continue
        if any(existing["heading"].lower() == heading.lower() for existing in sections):
            index += 1
            continue
        section_lines: list[str] = []
        cursor = content_start
        while cursor < len(lines):
            line = lines[cursor]
            if number_only_pattern.match(line) or heading_pattern.match(line):
                break
            if not _is_pdf_page_noise(line, heading):
                section_lines.append(line)
            if len(" ".join(section_lines)) >= max_chars:
                break
            cursor += 1
        excerpt = " ".join(section_lines).strip()
        if excerpt and len(excerpt) > 80:
            sections.append({"heading": heading, "excerpt": excerpt[:max_chars]})
        index += 1
    return sections


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _looks_like_heading_continuation(line: str) -> bool:
    if re.match(r"^\d+(?:\.\d+)*\s*", line):
        return False
    if len(line) > 80 or line.endswith((".", "?", "!")):
        return False
    words = line.split()
    if not words:
        return False
    titled = sum(1 for word in words if word[:1].isupper())
    return titled >= max(1, len(words) - 1)


def _is_pdf_page_noise(line: str, current_heading: str) -> bool:
    compact = " ".join(line.split())
    upper = compact.upper()
    if compact.isdigit():
        return True
    if upper in {"BIOLOGY", "THE LIVING WORLD"}:
        return True
    if upper.startswith("CHAPTER") or upper.startswith("REPRINT"):
        return True
    if compact.lower() in current_heading.lower():
        return True
    if re.match(r"^\d+(?:\.\d+)+\s+", compact):
        return True
    return False
