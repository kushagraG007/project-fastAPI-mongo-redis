"""
Unit tests for Pydantic models.
"""

import pytest
from pydantic import ValidationError
from app.models import DocumentCreate, DocumentStatus


def test_document_create_valid():
    """Test valid document creation"""
    doc = DocumentCreate(
        user_id="user_123",
        title="Test Document",
        content="This is test content"
    )
    
    assert doc.user_id == "user_123"
    assert doc.title == "Test Document"
    assert doc.content == "This is test content"


def test_document_create_missing_field():
    """Test validation fails when required field missing"""
    with pytest.raises(ValidationError) as exc_info:
        DocumentCreate(
            user_id="user_123",
            title="Test Document"
            # Missing content
        )
    
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("content",) for e in errors)


def test_document_create_empty_title():
    """Test validation fails for empty title"""
    with pytest.raises(ValidationError):
        DocumentCreate(
            user_id="user_123",
            title="",
            content="Content"
        )


def test_document_create_whitespace_stripping():
    """Test whitespace is stripped from fields"""
    doc = DocumentCreate(
        user_id="  user_123  ",
        title="  Test Document  ",
        content="  Test content  "
    )
    
    assert doc.user_id == "user_123"
    assert doc.title == "Test Document"
    assert doc.content == "Test content"


def test_content_hash_generation():
    """Test content hash is deterministic"""
    doc1 = DocumentCreate(
        user_id="user_123",
        title="Test",
        content="Same content"
    )
    
    doc2 = DocumentCreate(
        user_id="user_456",
        title="Different Title",
        content="Same content"
    )
    
    # Same content should produce same hash
    assert doc1.compute_content_hash() == doc2.compute_content_hash()


def test_content_hash_different_content():
    """Test different content produces different hash"""
    doc1 = DocumentCreate(
        user_id="user_123",
        title="Test",
        content="Content 1"
    )
    
    doc2 = DocumentCreate(
        user_id="user_123",
        title="Test",
        content="Content 2"
    )
    
    assert doc1.compute_content_hash() != doc2.compute_content_hash()


def test_document_status_enum():
    """Test DocumentStatus enum values"""
    assert DocumentStatus.QUEUED.value == "queued"
    assert DocumentStatus.PROCESSING.value == "processing"
    assert DocumentStatus.COMPLETED.value == "completed"
    assert DocumentStatus.FAILED.value == "failed"