from __future__ import annotations

from datetime import date
from typing import Any


def get_app_status() -> dict[str, object]:
    return {
        "mode": "Offline-first",
        "backend": "Not connected",
        "last_sync": "Local only",
    }


def get_dashboard_data() -> dict[str, Any]:
    return {
        "metrics": {
            "Documents": "0",
            "Concepts": "0",
            "Quizzes": "0",
            "Study streak": "0 days",
        },
        "recent_activity": [
            {"Time": "Pending", "Activity": "Connect backend upload queue", "Status": "Ready"},
            {"Time": "Pending", "Activity": "Connect local search index", "Status": "Ready"},
            {"Time": "Pending", "Activity": "Connect progress tracking", "Status": "Ready"},
        ],
        "next_actions": [
            "Upload first source document",
            "Review extracted concepts",
            "Generate first quiz",
            "Create revision plan",
        ],
    }


def get_progress_data() -> dict[str, Any]:
    return {
        "subjects": [
            {"subject": "Biology", "completion": 0},
            {"subject": "Physics", "completion": 0},
            {"subject": "Chemistry", "completion": 0},
        ]
    }


def queue_upload(files: list[Any], upload_kind: str, subject: str, tags: list[str], run_ai: bool) -> dict[str, object]:
    if not files:
        return {"ok": False, "message": "No files selected."}

    file_count = len(files)
    noun = "file" if file_count == 1 else "files"
    return {
        "ok": True,
        "message": f"Queued {file_count} {upload_kind} {noun} for local processing.",
        "metadata": {"subject": subject, "tags": tags, "run_ai": run_ai},
    }


def search_knowledge_base(filters: dict[str, object]) -> list[dict[str, object]]:
    query = str(filters["query"]).strip()
    if not query:
        return []

    return [
        {
            "id": "result-1",
            "title": f"Concept match for '{query}'",
            "subject": "Biology",
            "source": "Backend placeholder",
            "score": 94,
            "snippet": "Search results will be populated by SQLite FTS or the retrieval backend when connected.",
        },
        {
            "id": "result-2",
            "title": "Related definition",
            "subject": "Physics",
            "source": "Backend placeholder",
            "score": 81,
            "snippet": "This card demonstrates the final UI contract for ranked search result rendering.",
        },
    ]


def get_graph_preview() -> dict[str, Any]:
    return {
        "nodes": [
            {"id": "photosynthesis", "label": "Photosynthesis", "subject": "Biology", "position": [0.1, 0.8]},
            {"id": "chlorophyll", "label": "Chlorophyll", "subject": "Biology", "position": [0.38, 0.58]},
            {"id": "energy", "label": "Energy", "subject": "Biology", "position": [0.72, 0.8]},
            {"id": "force", "label": "Force", "subject": "Physics", "position": [0.2, 0.24]},
            {"id": "motion", "label": "Motion", "subject": "Physics", "position": [0.55, 0.2]},
            {"id": "work", "label": "Work", "subject": "Physics", "position": [0.82, 0.38]},
        ],
        "edges": [
            {"source": "photosynthesis", "target": "chlorophyll", "strength": 90},
            {"source": "photosynthesis", "target": "energy", "strength": 72},
            {"source": "force", "target": "motion", "strength": 85},
            {"source": "motion", "target": "work", "strength": 58},
        ],
    }


def generate_revision_plan(subject: str, exam_date: date, daily_minutes: int, focus: list[str]) -> list[dict[str, object]]:
    focus_text = ", ".join(focus) if focus else "core concepts"
    return [
        {
            "day": "Day 1",
            "title": f"{subject}: map the syllabus",
            "work": f"Review uploaded concepts, mark weak areas, and collect {focus_text}.",
            "minutes": daily_minutes,
            "load": 35,
        },
        {
            "day": "Day 2",
            "title": "Active recall",
            "work": "Answer generated questions and revisit every missed definition.",
            "minutes": daily_minutes,
            "load": 65,
        },
        {
            "day": "Day 3",
            "title": f"Exam rehearsal before {exam_date}",
            "work": "Run a mixed quiz, summarize gaps, and export the final checklist.",
            "minutes": daily_minutes,
            "load": 85,
        },
    ]


def generate_quiz(subject: str, question_count: int, difficulty: str, modes: list[str]) -> list[dict[str, object]]:
    return [
        {
            "prompt": f"Which option best describes a key {subject} concept?",
            "options": ["Stored definition", "Unrelated term", "File metadata", "Upload status"],
            "answer": "Stored definition",
            "source": f"{difficulty} | {', '.join(modes) if modes else 'General'} | Backend placeholder",
        }
        for _ in range(question_count)
    ]


def save_settings(settings: dict[str, object]) -> dict[str, object]:
    return {"ok": True, "message": "Settings saved in session placeholder. Backend persistence can attach here.", "settings": settings}
