"""Tests for database module."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.database.connection import close_connection, get_connection
from src.database.repository import (
    create_document,
    create_subject,
    get_all_subjects,
    get_document,
    get_document_stats,
    get_or_create_subject,
    update_document_status,
)
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        monkeypatch.setenv("NEURONOTE_DB_PATH", str(db_path))

        # Re-initialize connection with new path
        close_connection()

        # Initialize schema
        from src.database.schema import initialize_database

        initialize_database()

        yield db_path
        close_connection()


class TestDatabaseConnection:
    """Test database connection management."""

    def test_get_connection_returns_sqlite_connection(self, temp_db):
        """Test that get_connection returns a valid SQLite connection."""
        conn = get_connection()
        assert isinstance(conn, sqlite3.Connection)
        assert conn is not None

    def test_connection_has_wal_mode(self, temp_db):
        """Test that WAL mode is enabled."""
        conn = get_connection()
        cursor = conn.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        assert mode == "wal"

    def test_connection_has_foreign_keys(self, temp_db):
        """Test that foreign keys are enabled."""
        conn = get_connection()
        cursor = conn.execute("PRAGMA foreign_keys;")
        assert cursor.fetchone()[0] == 1


class TestSubjectRepository:
    """Test subject CRUD operations."""

    def test_create_subject(self, temp_db):
        """Test creating a new subject."""
        import uuid
        unique_name = f"Mathematics_{uuid.uuid4().hex[:8]}"
        subject_id = create_subject(unique_name, "Math and calculus")
        assert subject_id > 0

    def test_get_or_create_subject_new(self, temp_db):
        """Test creating a subject that doesn't exist."""
        subject_id = get_or_create_subject("Physics")
        assert subject_id > 0

    def test_get_or_create_subject_existing(self, temp_db):
        """Test retrieving an existing subject."""
        id1 = get_or_create_subject("Chemistry")
        id2 = get_or_create_subject("Chemistry")
        assert id1 == id2

    def test_get_all_subjects(self, temp_db):
        """Test retrieving all subjects."""
        import uuid
        bio_name = f"Biology_{uuid.uuid4().hex[:8]}"
        hist_name = f"History_{uuid.uuid4().hex[:8]}"
        create_subject(bio_name)
        create_subject(hist_name)
        subjects = get_all_subjects()
        assert len(subjects) >= 2


class TestDocumentRepository:
    """Test document CRUD operations."""

    def test_create_document(self, temp_db):
        """Test creating a document."""
        doc_id = create_document(
            title="Test Document",
            file_type="pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
        )
        assert doc_id > 0

    def test_update_document_status(self, temp_db):
        """Test updating document status."""
        doc_id = create_document(
            title="Test",
            file_type="text",
            file_path="/tmp/test.txt",
            file_size=100,
        )
        update_document_status(doc_id, "completed", raw_text="Test content")
        doc = get_document(doc_id)
        assert doc["status"] == "completed"
        assert doc["raw_text"] == "Test content"

    def test_get_document_stats(self, temp_db):
        """Test getting document statistics."""
        create_document("Doc1", "pdf", "/tmp/1.pdf", 100)
        create_document("Doc2", "pdf", "/tmp/2.pdf", 200)
        stats = get_document_stats()
        assert stats["total"] >= 2
        assert "pending" in stats
