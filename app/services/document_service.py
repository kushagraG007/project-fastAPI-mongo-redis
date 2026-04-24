"""
Business logic for document operations.
Coordinates between database, cache, and rate limiter.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
import redis
from bson import ObjectId
from typing import Optional
from datetime import datetime
from loguru import logger

from app.models import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    DocumentStatus,
    document_db_to_response,
    create_document_dict
)
from app.services.cache_service import CacheService
from app.services.rate_limiter import RateLimiter
from app.exceptions import RateLimitExceeded, DocumentNotFound  # ← Add this


class DocumentService:
    """Service layer for document operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase, redis_client: redis.Redis):
        self.db = db
        self.cache = CacheService(redis_client)
        self.rate_limiter = RateLimiter(redis_client)
        self.collection = db.documents
    
    async def create_document(self, doc_create: DocumentCreate) -> DocumentResponse:
        """Create a new document"""
        # Step 1: Rate limit check
        if not self.rate_limiter.check_and_increment(doc_create.user_id):
            raise RateLimitExceeded(doc_create.user_id, self.rate_limiter.max_jobs)  # ← Changed
        
        # Step 2: Check cache
        content_hash = doc_create.compute_content_hash()
        cached_summary = self.cache.get_cached_summary(content_hash)
        
        if cached_summary:
            logger.info(f"Returning cached result for user {doc_create.user_id}")
            self.rate_limiter.decrement(doc_create.user_id)
            
            now = datetime.utcnow()
            doc_dict = create_document_dict(doc_create)
            doc_dict["status"] = DocumentStatus.COMPLETED.value
            doc_dict["summary"] = cached_summary
            doc_dict["processing_completed_at"] = now
            
            result = await self.collection.insert_one(doc_dict)
            doc_dict["_id"] = result.inserted_id
            
            return document_db_to_response(doc_dict)
        
        # Step 3: No cache - insert as queued
        logger.info(f"Creating new document for user {doc_create.user_id}")
        doc_dict = create_document_dict(doc_create)
        
        result = await self.collection.insert_one(doc_dict)
        doc_dict["_id"] = result.inserted_id
        
        return document_db_to_response(doc_dict)
    
    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """Get document by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(document_id)})
            if doc:
                return document_db_to_response(doc)
            raise DocumentNotFound(document_id)  # ← Changed
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            if isinstance(e, DocumentNotFound):
                raise
            return None
    
    async def list_user_documents(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        status: Optional[DocumentStatus] = None
    ) -> DocumentListResponse:
        """List documents for a user with pagination"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status.value
        
        total = await self.collection.count_documents(query)
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)
        
        documents = [document_db_to_response(doc) for doc in docs]
        
        return DocumentListResponse(
            documents=documents,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )