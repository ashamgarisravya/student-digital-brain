"""Repository layer for NeuroNote database operations."""

import json
from datetime import date
from typing import Any, Dict, List, Optional

from src.database.connection import get_db
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


# ──────────────────────────────────────────────
# Documents
# ──────────────────────────────────────────────


def create_document(
    title: str,
    file_type: str,
    file_path: str,
    file_size: int,
    subject_id: Optional[int] = None,
    page_count: int = 0,
) -> int:
    """Insert a new document record.

    Args:
        title: Document title.
        file_type: One of 'pdf', 'image', 'audio', 'text'.
        file_path: Path to the uploaded file.
        file_size: File size in bytes.
        subject_id: Optional subject association.
        page_count: Number of pages (for PDF).

    Returns:
        The new document ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO documents (title, file_type, file_path, file_size,
               subject_id, page_count, status)
               VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
            (title, file_type, file_path, file_size, subject_id, page_count),
        )
        doc_id = cursor.lastrowid
        logger.info("Created document %d: %s (%s)", doc_id, title, file_type)
        return doc_id


def update_document_status(
    doc_id: int,
    status: str,
    error_message: Optional[str] = None,
    raw_text: Optional[str] = None,
) -> None:
    """Update document processing status.

    Args:
        doc_id: Document ID.
        status: New status ('pending', 'processing', 'completed', 'failed').
        error_message: Error details if failed.
        raw_text: Extracted raw text if completed.
    """
    fields = ["status = ?"]
    values: List[Any] = [status]

    if error_message is not None:
        fields.append("error_message = ?")
        values.append(error_message)
    if raw_text is not None:
        fields.append("raw_text = ?")
        values.append(raw_text)
    if status == "completed":
        fields.append("processed_at = CURRENT_TIMESTAMP")

    values.append(doc_id)
    query = f"UPDATE documents SET {', '.join(fields)} WHERE id = ?"

    with get_db() as conn:
        conn.execute(query, values)
        logger.info("Document %d status updated to '%s'", doc_id, status)


def get_document(doc_id: int) -> Optional[Dict[str, Any]]:
    """Get a single document by ID.

    Args:
        doc_id: Document ID.

    Returns:
        Document dict or None if not found.
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_documents(
    status: Optional[str] = None,
    file_type: Optional[str] = None,
    subject_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get documents with optional filters.

    Args:
        status: Filter by status.
        file_type: Filter by file type.
        subject_id: Filter by subject.
        limit: Maximum results.
        offset: Pagination offset.

    Returns:
        List of document dicts.
    """
    conditions: List[str] = []
    values: List[Any] = []

    if status:
        conditions.append("status = ?")
        values.append(status)
    if file_type:
        conditions.append("file_type = ?")
        values.append(file_type)
    if subject_id is not None:
        conditions.append("subject_id = ?")
        values.append(subject_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM documents {where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    values.extend([limit, offset])

    with get_db() as conn:
        cursor = conn.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]


def get_document_stats() -> Dict[str, Any]:
    """Get document processing statistics.

    Returns:
        Dict with total, pending, processing, completed, failed counts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT status, COUNT(*) as count FROM documents
               GROUP BY status"""
        )
        stats = {row["status"]: row["count"] for row in cursor.fetchall()}
    return {
        "total": sum(stats.values()),
        "pending": stats.get("pending", 0),
        "processing": stats.get("processing", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
    }


# ──────────────────────────────────────────────
# Subjects
# ──────────────────────────────────────────────


def create_subject(name: str, description: Optional[str] = None) -> int:
    """Create a new subject.

    Args:
        name: Subject name.
        description: Optional description.

    Returns:
        Subject ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO subjects (name, description) VALUES (?, ?)",
            (name, description),
        )
        logger.info("Created subject: %s", name)
        return cursor.lastrowid


def get_or_create_subject(name: str) -> int:
    """Get subject ID by name, creating it if it does not exist.

    Args:
        name: Subject name.

    Returns:
        Subject ID.
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT id FROM subjects WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor = conn.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
        return cursor.lastrowid


def get_all_subjects() -> List[Dict[str, Any]]:
    """Get all subjects with document and definition counts.

    Returns:
        List of subject dicts with counts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT s.*,
                      COUNT(DISTINCT d.id) as document_count,
                      COUNT(DISTINCT def.id) as definition_count
               FROM subjects s
               LEFT JOIN documents d ON d.subject_id = s.id
               LEFT JOIN definitions def ON def.subject_id = s.id
               GROUP BY s.id
               ORDER BY s.name"""
        )
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Topics
# ──────────────────────────────────────────────


def create_topic(
    name: str,
    subject_id: int,
    description: Optional[str] = None,
    parent_topic_id: Optional[int] = None,
    order_index: int = 0,
) -> int:
    """Create a new topic.

    Args:
        name: Topic name.
        subject_id: Parent subject ID.
        description: Optional description.
        parent_topic_id: Optional parent topic.
        order_index: Display order.

    Returns:
        Topic ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO topics (name, subject_id, description,
               parent_topic_id, order_index)
               VALUES (?, ?, ?, ?, ?)""",
            (name, subject_id, description, parent_topic_id, order_index),
        )
        return cursor.lastrowid


def get_topics_by_subject(subject_id: int) -> List[Dict[str, Any]]:
    """Get all topics for a subject.

    Args:
        subject_id: Subject ID.

    Returns:
        List of topic dicts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT t.*, COUNT(DISTINCT d.id) as definition_count
               FROM topics t
               LEFT JOIN definitions d ON d.topic_id = t.id
               WHERE t.subject_id = ?
               GROUP BY t.id
               ORDER BY t.order_index""",
            (subject_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Definitions
# ──────────────────────────────────────────────


def create_definition(
    term: str,
    definition: str,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    document_id: Optional[int] = None,
    importance: str = "medium",
    context: Optional[str] = None,
    source_page: Optional[int] = None,
) -> int:
    """Create a new concept definition.

    Args:
        term: Concept term.
        definition: Definition text.
        subject_id: Optional subject.
        topic_id: Optional topic.
        document_id: Optional source document.
        importance: 'high', 'medium', or 'low'.
        context: Surrounding context text.
        source_page: Source page number.

    Returns:
        Definition ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO definitions (term, definition, subject_id,
               topic_id, document_id, importance, context, source_page)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (term, definition, subject_id, topic_id, document_id, importance, context, source_page),
        )
        return cursor.lastrowid


def search_definitions(
    query: str,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search definitions by term or content.

    Args:
        query: Search query.
        subject_id: Optional subject filter.
        topic_id: Optional topic filter.
        limit: Maximum results.

    Returns:
        List of definition dicts.
    """
    conditions = ["(term LIKE ? OR definition LIKE ?)"]
    values: List[Any] = [f"%{query}%", f"%{query}%"]

    if subject_id is not None:
        conditions.append("subject_id = ?")
        values.append(subject_id)
    if topic_id is not None:
        conditions.append("topic_id = ?")
        values.append(topic_id)

    where = " AND ".join(conditions)
    sql = f"""SELECT def.*, s.name as subject_name, t.name as topic_name
              FROM definitions def
              LEFT JOIN subjects s ON def.subject_id = s.id
              LEFT JOIN topics t ON def.topic_id = t.id
              WHERE {where}
              ORDER BY def.importance DESC, def.term
              LIMIT ?"""
    values.append(limit)

    with get_db() as conn:
        cursor = conn.execute(sql, values)
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Questions
# ──────────────────────────────────────────────


def create_question(
    question_text: str,
    answer: str,
    question_type: str,
    difficulty: str = "medium",
    options: Optional[List[str]] = None,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    document_id: Optional[int] = None,
    explanation: Optional[str] = None,
) -> int:
    """Create a new quiz question.

    Args:
        question_text: The question.
        answer: Correct answer.
        question_type: 'multiple_choice', 'true_false', 'short_answer'.
        difficulty: 'easy', 'medium', 'hard'.
        options: MCQ options as list of strings.
        subject_id: Optional subject.
        topic_id: Optional topic.
        document_id: Optional source document.
        explanation: Optional answer explanation.

    Returns:
        Question ID.
    """
    options_json = json.dumps(options) if options else None
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO questions (question_text, answer, options,
               question_type, difficulty, subject_id, topic_id,
               document_id, explanation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                question_text,
                answer,
                options_json,
                question_type,
                difficulty,
                subject_id,
                topic_id,
                document_id,
                explanation,
            ),
        )
        return cursor.lastrowid


def get_questions_for_quiz(
    subject_id: int,
    topic_id: Optional[int] = None,
    count: int = 10,
    difficulty: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get random questions for quiz generation.

    Args:
        subject_id: Subject ID.
        topic_id: Optional topic filter.
        count: Number of questions.
        difficulty: Optional difficulty filter.

    Returns:
        List of question dicts with parsed options.
    """
    conditions = ["subject_id = ?"]
    values: List[Any] = [subject_id]

    if topic_id is not None:
        conditions.append("topic_id = ?")
        values.append(topic_id)
    if difficulty:
        conditions.append("difficulty = ?")
        values.append(difficulty)

    where = " AND ".join(conditions)
    sql = f"SELECT * FROM questions WHERE {where} ORDER BY RANDOM() LIMIT ?"
    values.append(count)

    with get_db() as conn:
        cursor = conn.execute(sql, values)
        questions = []
        for row in cursor.fetchall():
            q = dict(row)
            if q.get("options"):
                q["options"] = json.loads(q["options"])
            questions.append(q)
        return questions


# ──────────────────────────────────────────────
# Knowledge Links
# ──────────────────────────────────────────────


def create_knowledge_link(
    source_concept_id: int,
    target_concept_id: int,
    relationship_type: str,
    weight: float = 1.0,
) -> int:
    """Create a relationship between two concepts.

    Args:
        source_concept_id: Source definition ID.
        target_concept_id: Target definition ID.
        relationship_type: Relationship type.
        weight: Relationship strength (0.0-1.0).

    Returns:
        Link ID.
    """
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO knowledge_links
                   (source_concept_id, target_concept_id,
                    relationship_type, weight)
                   VALUES (?, ?, ?, ?)""",
                (source_concept_id, target_concept_id, relationship_type, weight),
            )
            return cursor.lastrowid or 0
        except Exception as e:
            logger.warning("Failed to create knowledge link: %s", e)
            return 0


def get_knowledge_graph_edges(
    subject_id: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """Get knowledge graph edges with concept names.

    Args:
        subject_id: Optional subject filter.
        limit: Maximum edges.

    Returns:
        List of edge dicts with source/target terms.
    """
    if subject_id is not None:
        sql = """SELECT kl.*, d1.term as source_term, d2.term as target_term
                 FROM knowledge_links kl
                 JOIN definitions d1 ON kl.source_concept_id = d1.id
                 JOIN definitions d2 ON kl.target_concept_id = d2.id
                 WHERE d1.subject_id = ? OR d2.subject_id = ?
                 ORDER BY kl.weight DESC
                 LIMIT ?"""
        values: List[Any] = [subject_id, subject_id, limit]
    else:
        sql = """SELECT kl.*, d1.term as source_term, d2.term as target_term
                 FROM knowledge_links kl
                 JOIN definitions d1 ON kl.source_concept_id = d1.id
                 JOIN definitions d2 ON kl.target_concept_id = d2.id
                 ORDER BY kl.weight DESC
                 LIMIT ?"""
        values = [limit]

    with get_db() as conn:
        cursor = conn.execute(sql, values)
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Quiz History
# ──────────────────────────────────────────────


def save_quiz_result(
    subject_id: Optional[int],
    topic_id: Optional[int],
    question_count: int,
    correct_count: int,
    score_percentage: float,
    questions: List[Dict[str, Any]],
    answers: Optional[List[str]] = None,
    duration_seconds: Optional[int] = None,
) -> int:
    """Save a completed quiz result.

    Args:
        subject_id: Subject ID.
        topic_id: Optional topic ID.
        question_count: Total questions.
        correct_count: Correct answers.
        score_percentage: Score percentage.
        questions: List of question dicts.
        answers: List of user answers.
        duration_seconds: Time taken.

    Returns:
        Quiz history ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO quiz_history (subject_id, topic_id,
               question_count, correct_count, score_percentage,
               questions, answers, duration_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                subject_id,
                topic_id,
                question_count,
                correct_count,
                score_percentage,
                json.dumps(questions),
                json.dumps(answers) if answers else None,
                duration_seconds,
            ),
        )
        return cursor.lastrowid


def get_quiz_history(subject_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Get quiz attempt history.

    Args:
        subject_id: Optional subject filter.
        limit: Maximum results.

    Returns:
        List of quiz history dicts.
    """
    if subject_id is not None:
        sql = """SELECT * FROM quiz_history WHERE subject_id = ?
                 ORDER BY taken_at DESC LIMIT ?"""
        values: List[Any] = [subject_id, limit]
    else:
        sql = "SELECT * FROM quiz_history ORDER BY taken_at DESC LIMIT ?"
        values = [limit]

    with get_db() as conn:
        cursor = conn.execute(sql, values)
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Revision History
# ──────────────────────────────────────────────


def create_revision_session(
    subject_id: int,
    topic_id: Optional[int],
    planned_date: date,
    duration_minutes: int = 60,
) -> int:
    """Create a planned revision session.

    Args:
        subject_id: Subject ID.
        topic_id: Optional topic ID.
        planned_date: Scheduled date.
        duration_minutes: Duration in minutes.

    Returns:
        Revision session ID.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO revision_history (subject_id, topic_id,
               planned_date, duration_minutes)
               VALUES (?, ?, ?, ?)""",
            (subject_id, topic_id, planned_date.isoformat(), duration_minutes),
        )
        return cursor.lastrowid


def get_revision_plan(
    subject_id: int,
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """Get revision sessions within a date range.

    Args:
        subject_id: Subject ID.
        start_date: Range start.
        end_date: Range end.

    Returns:
        List of revision session dicts.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT rh.*, s.name as subject_name, t.name as topic_name
               FROM revision_history rh
               LEFT JOIN subjects s ON rh.subject_id = s.id
               LEFT JOIN topics t ON rh.topic_id = t.id
               WHERE rh.subject_id = ?
               AND rh.planned_date BETWEEN ? AND ?
               ORDER BY rh.planned_date""",
            (subject_id, start_date.isoformat(), end_date.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]
