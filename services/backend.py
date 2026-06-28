from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from neuronote.api import (
    evaluate_answer,
    extract_topics,
    generate_question_bank,
    generate_quiz,
    generate_revision_plan,
    generate_structured_json,
    get_dashboard_stats,
    get_pdf_options,
    get_revision_source_data,
    process_audio,
    process_document,
    process_image,
    save_document,
    search_all,
    search_keyword,
    search_subject,
    search_topics,
)

__all__ = [
    "evaluate_answer",
    "extract_topics",
    "generate_quiz",
    "generate_question_bank",
    "generate_revision_plan",
    "generate_structured_json",
    "get_app_status",
    "get_dashboard_data",
    "get_dashboard_stats",
    "get_pdf_options",
    "get_progress_data",
    "get_revision_source_data",
    "process_audio",
    "process_document",
    "process_image",
    "save_document",
    "save_settings",
    "search_all",
    "search_keyword",
    "search_subject",
    "search_topics",
]


def get_app_status() -> dict[str, object]:
    return {
        "mode": "Offline-first",
        "backend": "Ollama + SQLite",
        "last_sync": "Local only",
        "storage": "Local workspace",
    }


def get_dashboard_data() -> dict[str, Any]:
    return get_dashboard_stats()


def get_progress_data() -> dict[str, Any]:
    return {"subjects": get_dashboard_stats().get("subjects", [])}


def save_settings(settings: dict[str, object]) -> dict[str, object]:
    return {"ok": True, "message": "Settings accepted by backend facade.", "settings": settings}
