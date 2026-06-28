from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .ollama import ollama_generate_json
from .prompts import structured_extraction_prompt

STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "because",
    "between",
    "from",
    "have",
    "into",
    "that",
    "their",
    "there",
    "this",
    "with",
    "which",
    "will",
}


def extract_topics(text: str, limit: int = 12) -> list[str]:
    """Extract topic labels. Ollama is used for rich extraction; this fallback is for resilience."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text.lower())
    candidates = [word.title() for word in words if word not in STOPWORDS]
    topics: list[str] = []
    for word, _ in Counter(candidates).most_common(limit * 2):
        if word not in topics:
            topics.append(word)
        if len(topics) == limit:
            break
    return topics


def generate_structured_json(text: str, metadata: dict[str, object] | None = None) -> dict[str, Any]:
    """Use local Ollama to map PDF text to the NeuroNote schema."""
    metadata = metadata or {}
    parsed = ollama_generate_json(structured_extraction_prompt(text, metadata), timeout=300)
    if parsed:
        return _normalize_structured(parsed, text, metadata, engine="ollama")
    return _fallback_json(text, metadata)


def _fallback_json(text: str, metadata: dict[str, object] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    topics = extract_topics(text)
    subject = str(metadata.get("subject") or (topics[0] if topics else "General"))
    topic = str(metadata.get("topic") or (topics[1] if len(topics) > 1 else subject))
    sentences = _sentences(text)
    concepts: list[dict[str, Any]] = []
    for index, concept in enumerate(topics[:12], start=1):
        sentence = next((item for item in sentences if concept.lower() in item.lower()), "")
        definition = sentence or f"{concept} is mentioned in the uploaded PDF."
        concepts.append(
            {
                "concept": concept,
                "definition": definition,
                "meaning": definition,
                "explanation": definition,
                "example": "",
                "subject": subject,
                "topic": topic,
                "importance": "high" if index <= 5 else "medium",
                "related_concepts": [item for item in topics[:6] if item != concept],
            }
        )
    if not concepts and text.strip():
        concepts.append(
            {
                "concept": topic,
                "definition": text.strip()[:300],
                "meaning": text.strip()[:300],
                "explanation": text.strip()[:300],
                "example": "",
                "subject": subject,
                "topic": topic,
                "importance": "medium",
                "related_concepts": [],
            }
        )
    return {
        "source_name": str(metadata.get("source_name", "unknown")),
        "source_type": str(metadata.get("source_type", "pdf")),
        "source_path": str(metadata.get("source_path", "")),
        "pages": metadata.get("pages", []),
        "assets": metadata.get("assets", {}),
        "subject": subject,
        "topic": topic,
        "class": str(metadata.get("class") or metadata.get("grade") or ""),
        "summary": " ".join(sentences[:3])[:700],
        "topics": topics,
        "concepts": concepts,
        "study_notes": _fallback_study_notes(concepts),
        "raw_text": text,
        "engine": "ollama-unavailable-fallback",
        "source_rule": "Only the uploaded PDF text is used.",
    }


def _normalize_structured(
    parsed: dict[str, Any],
    text: str,
    metadata: dict[str, object],
    engine: str,
) -> dict[str, Any]:
    topics = [str(item) for item in parsed.get("topics", []) if str(item).strip()]
    concepts = []
    for item in parsed.get("concepts", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("concept", "")).strip()
        if not name:
            continue
        definition = str(item.get("definition") or item.get("meaning") or item.get("explanation") or "").strip()
        concepts.append(
            {
                "concept": name,
                "definition": definition,
                "meaning": str(item.get("meaning") or definition),
                "explanation": str(item.get("explanation") or definition),
                "example": str(item.get("example") or ""),
                "subject": str(parsed.get("subject") or metadata.get("subject") or "General"),
                "topic": str(parsed.get("topic") or metadata.get("topic") or "General"),
                "importance": str(item.get("importance") or "medium"),
                "related_concepts": [str(value) for value in item.get("related_concepts", [])],
            }
        )
    if not topics:
        topics = [str(item["concept"]) for item in concepts[:12]]
    return {
        "source_name": str(metadata.get("source_name", "unknown")),
        "source_type": str(metadata.get("source_type", "pdf")),
        "source_path": str(metadata.get("source_path", "")),
        "pages": metadata.get("pages", []),
        "assets": metadata.get("assets", {}),
        "subject": str(parsed.get("subject") or metadata.get("subject") or "General"),
        "topic": str(parsed.get("topic") or metadata.get("topic") or "General"),
        "class": str(metadata.get("class") or metadata.get("grade") or parsed.get("class") or ""),
        "summary": str(parsed.get("summary") or ""),
        "topics": topics,
        "concepts": concepts,
        "study_notes": parsed.get("study_notes") if isinstance(parsed.get("study_notes"), dict) else _fallback_study_notes(concepts),
        "raw_text": text,
        "engine": engine,
        "source_rule": "Only the uploaded PDF text is used.",
    }


def _fallback_study_notes(concepts: list[dict[str, Any]]) -> dict[str, list[str]]:
    definitions = [f"{item['concept']}: {item['definition']}" for item in concepts if item.get("definition")]
    names = [str(item["concept"]) for item in concepts]
    return {
        "Definitions": definitions,
        "Meanings": definitions,
        "Concepts": names,
        "Formulae": [],
        "Algorithms": [],
        "Hardware": [],
        "Software": [],
        "Examples": [str(item.get("example", "")) for item in concepts if item.get("example")],
        "Applications": [],
    }


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
