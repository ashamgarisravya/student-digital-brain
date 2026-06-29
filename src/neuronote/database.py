from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import get_settings

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    pdf_hash TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    summary TEXT NOT NULL DEFAULT '',
    raw_text TEXT NOT NULL DEFAULT '',
    structured_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    concept TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    importance TEXT NOT NULL DEFAULT 'medium',
    related_concepts TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    questions_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    subject TEXT NOT NULL DEFAULT 'General',
    topic TEXT NOT NULL DEFAULT 'General',
    plan_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT NOT NULL UNIQUE,
    query_json TEXT NOT NULL,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents(subject);
CREATE INDEX IF NOT EXISTS idx_documents_topic ON documents(topic);
CREATE INDEX IF NOT EXISTS idx_concepts_subject ON concepts(subject);
CREATE INDEX IF NOT EXISTS idx_concepts_topic ON concepts(topic);
CREATE INDEX IF NOT EXISTS idx_concepts_concept ON concepts(concept);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_settings().database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate_connection(conn)
    return conn


def _migrate_connection(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "documents", "pdf_hash", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "documents", "summary", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "quizzes", "document_id", "INTEGER")
    _ensure_column(conn, "revisions", "document_id", "INTEGER")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_pdf_hash ON documents(pdf_hash)")


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def reset_database(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
    with get_connection(db_path):
        pass


def save_document_record(structured: dict[str, Any], db_path: Path | None = None) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO documents (source_name, source_type, subject, topic, raw_text, structured_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                structured.get("source_name", "unknown"),
                structured.get("source_type", "text"),
                structured.get("subject", "General"),
                structured.get("topic", "General"),
                structured.get("raw_text", ""),
                json.dumps(structured, ensure_ascii=False),
            ),
        )
        document_id = int(cursor.lastrowid or 0)
        for concept in structured.get("concepts", []):
            conn.execute(
                """
                INSERT INTO concepts
                    (document_id, concept, definition, subject, topic, importance, related_concepts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    concept.get("concept", ""),
                    concept.get("definition", ""),
                    concept.get("subject", structured.get("subject", "General")),
                    concept.get("topic", structured.get("topic", "General")),
                    concept.get("importance", "medium"),
                    json.dumps(concept.get("related_concepts", []), ensure_ascii=False),
                ),
            )
        conn.commit()
        return document_id


def save_pdf_document_record(structured: dict[str, Any], pdf_hash: str, db_path: Path | None = None) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO documents (source_name, source_type, pdf_hash, subject, topic, summary, raw_text, structured_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                structured.get("source_name", "unknown"),
                "pdf",
                pdf_hash,
                structured.get("subject", "General"),
                structured.get("topic", "General"),
                structured.get("summary", ""),
                structured.get("raw_text", ""),
                json.dumps(structured, ensure_ascii=False),
            ),
        )
        document_id = int(cursor.lastrowid or 0)
        for concept in structured.get("concepts", []):
            conn.execute(
                """
                INSERT INTO concepts
                    (document_id, concept, definition, subject, topic, importance, related_concepts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    concept.get("concept", ""),
                    concept.get("definition", ""),
                    concept.get("subject", structured.get("subject", "General")),
                    concept.get("topic", structured.get("topic", "General")),
                    concept.get("importance", "medium"),
                    json.dumps(concept.get("related_concepts", []), ensure_ascii=False),
                ),
            )
        conn.commit()
        return document_id


def get_document_by_hash(pdf_hash: str, db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE pdf_hash = ? ORDER BY created_at DESC LIMIT 1",
            (pdf_hash,),
        ).fetchone()
        return dict(row) if row else None


def get_document(document_id: int, db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return dict(row) if row else None


def latest_pdf_document(db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE source_type = 'pdf' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def find_pdf_document(
    subject: str | None = None,
    topic: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    subject_pattern = f"%{subject}%" if subject else "%"
    topic_pattern = f"%{topic}%" if topic else "%"
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM documents
            WHERE source_type = 'pdf'
              AND LOWER(subject) LIKE LOWER(?)
              AND LOWER(topic) LIKE LOWER(?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (subject_pattern, topic_pattern),
        ).fetchone()
        return dict(row) if row else None


def list_documents(db_path: Path | None = None) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


def list_concepts(db_path: Path | None = None) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM concepts ORDER BY concept").fetchall()
        return [dict(row) for row in rows]


def search_concepts(field: str, value: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    allowed = {"subject", "topic", "concept", "definition"}
    if field not in allowed:
        raise ValueError(f"Unsupported search field: {field}")
    with get_connection(db_path) as conn:
        if field == "subject":
            rows = conn.execute(
                """
            SELECT c.*, d.source_name, d.source_type, d.structured_json
            FROM concepts c
            JOIN documents d ON d.id = c.document_id
            WHERE LOWER(c.subject) LIKE LOWER(?)
            ORDER BY c.importance, c.concept
            """,
                (f"%{value}%",),
            ).fetchall()
        elif field == "topic":
            rows = conn.execute(
                """
            SELECT c.*, d.source_name, d.source_type, d.structured_json
            FROM concepts c
            JOIN documents d ON d.id = c.document_id
            WHERE LOWER(c.topic) LIKE LOWER(?)
            ORDER BY c.importance, c.concept
            """,
                (f"%{value}%",),
            ).fetchall()
        elif field == "concept":
            rows = conn.execute(
                """
            SELECT c.*, d.source_name, d.source_type, d.structured_json
            FROM concepts c
            JOIN documents d ON d.id = c.document_id
            WHERE LOWER(c.concept) LIKE LOWER(?)
            ORDER BY c.importance, c.concept
            """,
                (f"%{value}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                """
            SELECT c.*, d.source_name, d.source_type, d.structured_json
            FROM concepts c
            JOIN documents d ON d.id = c.document_id
            WHERE LOWER(c.definition) LIKE LOWER(?)
            ORDER BY c.importance, c.concept
            """,
                (f"%{value}%",),
            ).fetchall()
        return [dict(row) for row in rows]


def keyword_search(keyword: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT c.*, d.source_name, d.source_type, d.structured_json
            FROM concepts c
            JOIN documents d ON d.id = c.document_id
            WHERE LOWER(c.concept) LIKE LOWER(?)
               OR LOWER(c.definition) LIKE LOWER(?)
               OR LOWER(d.raw_text) LIKE LOWER(?)
            ORDER BY c.concept
            """,
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
        ).fetchall()
        return [dict(row) for row in rows]


def search_documents(
    subject: str | None = None,
    topic: str | None = None,
    keyword: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    subject_pattern = f"%{subject}%" if subject else "%"
    topic_pattern = f"%{topic}%" if topic else "%"
    keyword_pattern = f"%{keyword}%" if keyword else "%"
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, source_name, source_type, subject, topic, raw_text, structured_json, created_at
            FROM documents
            WHERE LOWER(subject) LIKE LOWER(?)
              AND LOWER(topic) LIKE LOWER(?)
              AND LOWER(raw_text) LIKE LOWER(?)
            ORDER BY created_at DESC
            """,
            (subject_pattern, topic_pattern, keyword_pattern),
        ).fetchall()
        return [dict(row) for row in rows]


def save_quiz_record(
    subject: str,
    topic: str,
    questions: list[dict[str, Any]],
    db_path: Path | None = None,
    document_id: int | None = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO quizzes (document_id, subject, topic, questions_json) VALUES (?, ?, ?, ?)",
            (document_id, subject, topic, json.dumps(questions, ensure_ascii=False)),
        )
        conn.commit()
        return int(cursor.lastrowid or 0)


def latest_quiz_record(document_id: int | None = None, db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        if document_id is not None:
            row = conn.execute(
                "SELECT * FROM quizzes WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
                (document_id,),
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM quizzes ORDER BY created_at DESC LIMIT 1").fetchone()
        return dict(row) if row else None


def save_revision_record(
    subject: str,
    topic: str,
    plan: dict[str, Any] | list[dict[str, Any]],
    db_path: Path | None = None,
    document_id: int | None = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO revisions (document_id, subject, topic, plan_json) VALUES (?, ?, ?, ?)",
            (document_id, subject, topic, json.dumps(plan, ensure_ascii=False)),
        )
        conn.commit()
        return int(cursor.lastrowid or 0)


def latest_revision_record(document_id: int | None = None, db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        if document_id is not None:
            row = conn.execute(
                "SELECT * FROM revisions WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
                (document_id,),
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM revisions ORDER BY created_at DESC LIMIT 1").fetchone()
        return dict(row) if row else None


def get_search_cache(query_hash: str, db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT response_json FROM search_cache WHERE query_hash = ?",
            (query_hash,),
        ).fetchone()
        if not row:
            return None
        loaded = json.loads(str(row["response_json"]))
        return loaded if isinstance(loaded, dict) else None


def save_search_cache(
    query_hash: str,
    query: dict[str, Any],
    response: dict[str, Any],
    db_path: Path | None = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO search_cache (query_hash, query_json, response_json)
            VALUES (?, ?, ?)
            ON CONFLICT(query_hash) DO UPDATE SET response_json = excluded.response_json
            """,
            (query_hash, json.dumps(query, ensure_ascii=False), json.dumps(response, ensure_ascii=False)),
        )
        conn.commit()
        return int(cursor.lastrowid or 0)


def dashboard_counts(db_path: Path | None = None) -> dict[str, int]:
    with get_connection(db_path) as conn:
        return {
            "documents": int(conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]),
            "subjects": int(conn.execute("SELECT COUNT(DISTINCT subject) FROM documents").fetchone()[0]),
            "topics": int(conn.execute("SELECT COUNT(DISTINCT topic) FROM documents").fetchone()[0]),
            "quizzes": int(conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]),
            "revisions": int(conn.execute("SELECT COUNT(*) FROM revisions").fetchone()[0]),
        }
