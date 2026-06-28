"""SQLite database schema and initialization for NeuroNote."""

import sqlite3
from typing import List

from src.database.connection import get_db
from src.utils.logging import setup_logging

logger = setup_logging(__name__)

# Full DDL for all 10 tables
SCHEMA_SQL = """
-- 1. Subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT DEFAULT '#4A90D9',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK(file_type IN ('pdf', 'image', 'audio', 'text')),
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    page_count INTEGER DEFAULT 0,
    raw_text TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    subject_id INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
);

-- 3. Topics table
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    description TEXT,
    parent_topic_id INTEGER,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_topic_id) REFERENCES topics(id) ON DELETE SET NULL
);

-- 4. Definitions (concepts) table
CREATE TABLE IF NOT EXISTS definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    definition TEXT NOT NULL,
    subject_id INTEGER,
    topic_id INTEGER,
    document_id INTEGER,
    importance TEXT DEFAULT 'medium'
        CHECK(importance IN ('high', 'medium', 'low')),
    context TEXT,
    source_page INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 5. Questions table
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    answer TEXT NOT NULL,
    options TEXT,
    question_type TEXT NOT NULL
        CHECK(question_type IN ('multiple_choice', 'true_false', 'short_answer')),
    difficulty TEXT DEFAULT 'medium'
        CHECK(difficulty IN ('easy', 'medium', 'hard')),
    subject_id INTEGER,
    topic_id INTEGER,
    document_id INTEGER,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 6. Audio metadata table
CREATE TABLE IF NOT EXISTS audio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    duration_seconds REAL,
    transcript TEXT,
    model_used TEXT DEFAULT 'whisper.cpp',
    language TEXT DEFAULT 'en',
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 7. Images metadata table
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    ocr_text TEXT,
    image_type TEXT DEFAULT 'printed'
        CHECK(image_type IN ('printed', 'handwritten', 'whiteboard', 'screenshot')),
    ocr_confidence REAL,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 8. Knowledge links (graph edges) table
CREATE TABLE IF NOT EXISTS knowledge_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_concept_id INTEGER NOT NULL,
    target_concept_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL
        CHECK(relationship_type IN (
            'related_to', 'is_a', 'part_of', 'prerequisite',
            'example_of', 'contrasts_with', 'causes', 'used_in'
        )),
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_concept_id) REFERENCES definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (target_concept_id) REFERENCES definitions(id) ON DELETE CASCADE,
    UNIQUE(source_concept_id, target_concept_id, relationship_type)
);

-- 9. Quiz history table
CREATE TABLE IF NOT EXISTS quiz_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER,
    topic_id INTEGER,
    question_count INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    score_percentage REAL NOT NULL,
    questions TEXT NOT NULL,
    answers TEXT,
    duration_seconds INTEGER,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
);

-- 10. Revision history table
CREATE TABLE IF NOT EXISTS revision_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER,
    topic_id INTEGER,
    planned_date DATE NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    completed BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
);
"""

# Indexes for performance
INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);",
    "CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);",
    "CREATE INDEX IF NOT EXISTS idx_subjects_name ON subjects(name);",
    "CREATE INDEX IF NOT EXISTS idx_topics_subject ON topics(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_topics_parent ON topics(parent_topic_id);",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_topics_name_subject ON topics(name, subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_definitions_term ON definitions(term);",
    "CREATE INDEX IF NOT EXISTS idx_definitions_subject ON definitions(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_definitions_topic ON definitions(topic_id);",
    "CREATE INDEX IF NOT EXISTS idx_definitions_importance ON definitions(importance);",
    "CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic_id);",
    "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);",
    "CREATE INDEX IF NOT EXISTS idx_audio_document ON audio(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_images_document ON images(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_images_type ON images(image_type);",
    "CREATE INDEX IF NOT EXISTS idx_links_source ON knowledge_links(source_concept_id);",
    "CREATE INDEX IF NOT EXISTS idx_links_target ON knowledge_links(target_concept_id);",
    "CREATE INDEX IF NOT EXISTS idx_links_type ON knowledge_links(relationship_type);",
    "CREATE INDEX IF NOT EXISTS idx_quiz_subject ON quiz_history(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_quiz_taken ON quiz_history(taken_at);",
    "CREATE INDEX IF NOT EXISTS idx_revision_date ON revision_history(planned_date);",
    "CREATE INDEX IF NOT EXISTS idx_revision_completed ON revision_history(completed);",
]

# FTS5 full-text search virtual table
FTS5_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    raw_text,
    content='documents',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, raw_text)
    VALUES (new.id, new.title, new.raw_text);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, raw_text)
    VALUES ('delete', old.id, old.title, old.raw_text);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, raw_text)
    VALUES ('delete', old.id, old.title, old.raw_text);
    INSERT INTO documents_fts(rowid, title, raw_text)
    VALUES (new.id, new.title, new.raw_text);
END;
"""


def initialize_database() -> None:
    """Create all tables, indexes, and FTS5 virtual table.

    Safe to call multiple times; uses IF NOT EXISTS.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Create tables
        cursor.executescript(SCHEMA_SQL)
        logger.info("Database tables created successfully")

        # Create indexes
        for index_sql in INDEXES_SQL:
            cursor.execute(index_sql)
        logger.info("Database indexes created successfully")

        # Create FTS5 virtual table and triggers
        cursor.executescript(FTS5_SQL)
        logger.info("FTS5 full-text search initialized")

        conn.commit()

    logger.info("Database initialization complete")


def get_table_names() -> List[str]:
    """Get list of all table names in the database.

    Returns:
        List of table names.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        return [row["name"] for row in cursor.fetchall()]