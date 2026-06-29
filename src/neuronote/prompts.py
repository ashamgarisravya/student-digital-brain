from __future__ import annotations

from typing import Any

PDF_ONLY_RULES = """
You are NeuroNote, an offline study assistant. Use ONLY the uploaded PDF text.
If a requested fact is not present in the PDF, say it is not present.
Do not add outside knowledge, examples, formulas, or explanations.
Write clearly for school students from class 5 to class 12.
Return valid JSON only.
""".strip()


def structured_extraction_prompt(text: str, metadata: dict[str, object] | None = None) -> str:
    metadata = metadata or {}
    return f"""
{PDF_ONLY_RULES}

Task: Extract structured study material from this PDF.
Return this exact JSON shape:
{{
  "subject": "string",
  "topic": "string",
  "summary": "string",
  "topics": ["string"],
  "concepts": [
    {{
      "concept": "string",
      "definition": "string",
      "meaning": "string",
      "explanation": "string",
      "example": "string",
      "importance": "high|medium|low",
      "related_concepts": ["string"]
    }}
  ],
  "study_notes": {{
    "Definitions": ["string"],
    "Meanings": ["string"],
    "Concepts": ["string"],
    "Formulae": ["string"],
    "Algorithms": ["string"],
    "Hardware": ["string"],
    "Software": ["string"],
    "Examples": ["string"],
    "Applications": ["string"]
  }}
}}

Preferred subject: {metadata.get("subject") or "infer from PDF"}
Preferred topic/chapter: {metadata.get("topic") or "infer from PDF"}
Class/grade: {metadata.get("class") or metadata.get("grade") or "class 5 to 12"}

PDF text:
{_clip(text, 6500)}
""".strip()


def quiz_prompt(text: str, question_count: int = 20) -> str:
    return f"""
{PDF_ONLY_RULES}

Task: Generate exactly {question_count} multiple choice questions from the PDF text.
Requirements:
- Write questions at a class 5 to class 12 student level.
- Each question has four meaningful options labelled A, B, C, D.
- Exactly one option is correct.
- Wrong answers must be believable but clearly wrong according to the PDF.
- Do not repeat the same option set.
- Randomize the correct option position across questions.
- Cover Easy, Medium, and Hard difficulty levels.

Return this exact JSON shape:
{{
  "questions": [
    {{
      "question": "string",
      "options": {{"A": "string", "B": "string", "C": "string", "D": "string"}},
      "correct_answer": "A|B|C|D",
      "explanation": "string",
      "difficulty": "Easy|Medium|Hard"
    }}
  ]
}}

PDF text:
{_clip(text, 18000)}
""".strip()


def revision_prompt(text: str, subject: str = "General", topic: str = "General") -> str:
    return f"""
{PDF_ONLY_RULES}

Task: Build a complete revision companion from the PDF.
Audience: school students from class 5 to class 12.
Return this exact JSON shape:
{{
  "mind_map": {{
    "subject": "string",
    "chapter": "string",
    "topics": [
      {{"title": "string", "definition": "string", "related_concepts": ["string"]}}
    ]
  }},
  "important_topics": [
    {{"title": "string", "explanation": "string", "example": "string", "why_important": "string"}}
  ],
  "study_notes": {{
    "Definitions": ["string"],
    "Meanings": ["string"],
    "Concepts": ["string"],
    "Formulae": ["string"],
    "Algorithms": ["string"],
    "Hardware": ["string"],
    "Software": ["string"],
    "Examples": ["string"],
    "Applications": ["string"]
  }},
  "question_bank": {{
    "very_short": [{{"question": "string", "answer": "string", "explanation": "string"}}],
    "short": [{{"question": "string", "answer": "string", "explanation": "string"}}],
    "long": [{{"question": "string", "answer": "string", "explanation": "string"}}]
  }},
  "additional_reading": ["string"],
  "optional_topics": ["string"],
  "advanced_topics": ["string"]
}}

Requested subject: {subject}
Requested topic/chapter: {topic}

PDF text:
{_clip(text, 18000)}
""".strip()


def search_prompt(query: dict[str, str], documents: list[dict[str, Any]]) -> str:
    source_text = "\n\n".join(
        f"PDF: {doc.get('source_name')}\nSubject: {doc.get('subject')}\nTopic: {doc.get('topic')}\n{_clip(str(doc.get('raw_text', '')), 6000)}"
        for doc in documents[:3]
    )
    return f"""
{PDF_ONLY_RULES}

Task: Answer the search query using only the uploaded PDF text below.
Audience: school students from class 5 to class 12.
Return this exact JSON shape:
{{
  "present": true,
  "definition": "string",
  "meaning": "string",
  "explanation": "string",
  "examples": ["string"],
  "related_topics": ["string"],
  "source": "PDF file name or empty"
}}
If the information is not in the PDF, set "present": false and explain politely.

Search fields:
Subject: {query.get("subject", "")}
Topic: {query.get("topic", "")}
Keyword: {query.get("keyword", "")}
Concept: {query.get("concept", "")}
Definition: {query.get("definition", "")}
Meaning: {query.get("meaning", "")}

Uploaded PDF text:
{source_text}
""".strip()


def definition_prompt(text: str, concept: str) -> str:
    return f"""
{PDF_ONLY_RULES}

Task: Define this concept using only the PDF: {concept}
Return JSON with definition, meaning, explanation, examples, related_topics.

PDF text:
{_clip(text)}
""".strip()


def _clip(text: str, max_chars: int = 12000) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 20] + " ...[PDF text clipped]"
