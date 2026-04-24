"""
Document data models for API validation and database storage.

Pydantic models provide:
- Request validation (user input)
- Response serialization (API output)
- Type safety throughout the application
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum
import hashlib


# ============================================
# Enums
# ============================================

class DocumentStatus(str, Enum):
    """
    Document processing status.
    
    Flow: queued → processing → completed/failed
    """
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# Request Models (API Input)
# ============================================

class DocumentCreate(BaseModel):
    """
    Request model for creating a new document.
    
    Used in: POST /documents
    """
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the user",
        examples=["user_123"]
    )
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Document title",
        examples=["Q4 Sales Report"]
    )
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=100000,  # 100KB max
        description="Document content to be processed",
        examples=["This is the document content..."]
    )
    
    @field_validator('user_id', 'title', 'content')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace"""
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Ensure content is not empty after stripping"""
        if not v.strip():
            raise ValueError("Content cannot be empty or only whitespace")
        return v
    
    def compute_content_hash(self) -> str:
        """
        Generate SHA-256 hash of content for caching.
        
        Same content → same hash → cache hit
        """
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()


# ============================================
# Response Models (API Output)
# ============================================

class DocumentResponse(BaseModel):
    """
    Response model for document operations.
    
    Used in: POST /documents, GET /documents/{id}
    """
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        examples=["507f1f77bcf86cd799439011"]
    )
    
    user_id: str = Field(
        ...,
        description="User who created the document"
    )
    
    title: str = Field(
        ...,
        description="Document title"
    )
    
    status: DocumentStatus = Field(
        ...,
        description="Current processing status"
    )
    
    created_at: datetime = Field(
        ...,
        description="Document creation timestamp"
    )
    
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )
    
    summary: Optional[str] = Field(
        None,
        description="AI-generated summary (only present when status is 'completed')",
        examples=["This document discusses Q4 sales performance..."]
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error details (only present when status is 'failed')",
        examples=["Processing timeout after 30 seconds"]
    )
    
    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "document_id": "507f1f77bcf86cd799439011",
                "user_id": "user_123",
                "title": "Q4 Sales Report",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:25Z",
                "summary": "This document provides an overview of Q4 sales performance..."
            }
        }


class DocumentListResponse(BaseModel):
    """
    Response model for listing documents with pagination.
    
    Used in: GET /users/{user_id}/documents
    """
    documents: list[DocumentResponse] = Field(
        ...,
        description="List of documents"
    )
    
    total: int = Field(
        ...,
        description="Total number of documents matching the query",
        examples=[42]
    )
    
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        examples=[1]
    )
    
    page_size: int = Field(
        ...,
        description="Number of items per page",
        examples=[10]
    )
    
    total_pages: int = Field(
        ...,
        description="Total number of pages",
        examples=[5]
    )
    
    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "document_id": "507f1f77bcf86cd799439011",
                        "user_id": "user_123",
                        "title": "Q4 Sales Report",
                        "status": "completed",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:25Z",
                        "summary": "Summary text..."
                    }
                ],
                "total": 42,
                "page": 1,
                "page_size": 10,
                "total_pages": 5
            }
        }


# ============================================
# Database Models (MongoDB Storage)
# ============================================

class DocumentInDB(BaseModel):
    """
    Complete document model as stored in MongoDB.
    
    This includes all fields that exist in the database,
    including internal fields not exposed via API.
    """
    user_id: str
    title: str
    content: str
    content_hash: str  # SHA-256 hash for cache lookup
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    error_message: Optional[str] = None
    
    # Processing metadata
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    retry_count: int = 0  # For future retry logic
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True  # Store enum as string in MongoDB


# ============================================
# Utility Functions
# ============================================

def document_db_to_response(doc_dict: dict) -> DocumentResponse:
    """
    Convert MongoDB document to API response model.
    
    Args:
        doc_dict: Document from MongoDB (with _id as ObjectId)
    
    Returns:
        DocumentResponse: API response model
    """
    return DocumentResponse(
        document_id=str(doc_dict["_id"]),  # Convert ObjectId to string
        user_id=doc_dict["user_id"],
        title=doc_dict["title"],
        status=doc_dict["status"],
        created_at=doc_dict["created_at"],
        updated_at=doc_dict["updated_at"],
        summary=doc_dict.get("summary"),
        error_message=doc_dict.get("error_message")
    )


def create_document_dict(doc_create: DocumentCreate) -> dict:
    """
    Create MongoDB document dictionary from creation request.
    
    Args:
        doc_create: Validated document creation request
    
    Returns:
        dict: Document ready for MongoDB insertion
    """
    now = datetime.utcnow()
    
    return {
        "user_id": doc_create.user_id,
        "title": doc_create.title,
        "content": doc_create.content,
        "content_hash": doc_create.compute_content_hash(),
        "status": DocumentStatus.QUEUED.value,
        "created_at": now,
        "updated_at": now,
        "summary": None,
        "error_message": None,
        "processing_started_at": None,
        "processing_completed_at": None,
        "retry_count": 0
    }