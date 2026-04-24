"""
API endpoints for document operations.
"""

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis
from typing import Optional

from app.database.mongodb import get_db
from app.database.redis import get_redis
from app.models import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    DocumentStatus
)
from app.services import DocumentService

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def submit_document(
    document: DocumentCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Submit a document for processing.
    
    Rate Limit: Maximum 3 active jobs (queued + processing) per user.
    """
    service = DocumentService(db, redis_client)
    return await service.create_document(document)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document_status(
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get document status and summary (if completed)"""
    service = DocumentService(db, redis_client)
    return await service.get_document(document_id)


@router.get("/users/{user_id}/documents", response_model=DocumentListResponse)
async def list_user_documents(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """List all documents for a user with pagination"""
    service = DocumentService(db, redis_client)
    return await service.list_user_documents(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status
    )